import json
import base64
from pathlib import Path

from flask import Blueprint, jsonify, request
from jsonschema import validate, ValidationError
from sqlalchemy import and_, or_, func

from models import db, Book, Category

books_bp = Blueprint("books", __name__)

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "book.json"
)

with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
    BOOK_SCHEMA = json.load(file)


def validate_book(data, partial=False):
    if not isinstance(data, dict):
        return "Request body must be a JSON object."

    schema = dict(BOOK_SCHEMA)

    if partial:
        schema.pop("required", None)

    try:
        validate(instance=data, schema=schema)
    except ValidationError as error:
        return error.message

    if partial and not data:
        return "Request body must contain at least one field."

    return None


SORT_FIELDS = {
    "id": Book.id,
    "title": Book.title,
    "isbn": Book.isbn,
    "price_vnd": Book.price_vnd,
    "stock": Book.stock,
}


def encode_cursor(data):
    raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(token):
    padding = "=" * (-len(token) % 4)
    raw = base64.urlsafe_b64decode(token + padding)
    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("Invalid cursor.")

    if not isinstance(data.get("sort"), list):
        raise ValueError("Invalid cursor sort.")

    if not isinstance(data.get("values"), list):
        raise ValueError("Invalid cursor values.")

    return data

def parse_sort(raw_sort):
    sort_keys = []

    for item in raw_sort.split(","):
        item = item.strip()

        if not item:
            raise ValueError("Sort fields must not be empty.")

        descending = item.startswith("-")
        field = item[1:] if descending else item.lstrip("+")

        if field not in SORT_FIELDS:
            raise ValueError(
                f"Unsupported sort field: {field}. "
                f"Allowed fields: {', '.join(SORT_FIELDS)}."
            )

        if any(existing_field == field
               for existing_field, _ in sort_keys):
            raise ValueError(f"Duplicate sort field: {field}.")

        sort_keys.append((field, descending))

    if not any(field == "id" for field, _ in sort_keys):
        sort_keys.append(("id", False))

    return sort_keys

def apply_sort(query, sort_keys):
    order_clauses = []

    for field, descending in sort_keys:
        column = SORT_FIELDS[field]
        order_clauses.append(
            column.desc() if descending else column.asc()
        )

    return query.order_by(None).order_by(*order_clauses)

def apply_cursor_filter(query, sort_keys, values):
    if len(values) != len(sort_keys):
        raise ValueError("Cursor does not match the sort fields.")

    conditions = []
    equal_prefix = []

    for (field, descending), value in zip(sort_keys, values):
        column = SORT_FIELDS[field]

        if value is None:
            raise ValueError("Null cursor values are not supported.")

        comparison = column < value if descending else column > value

        conditions.append(
            and_(*equal_prefix, comparison)
        )
        equal_prefix.append(column == value)

    return query.filter(or_(*conditions))

@books_bp.get("")
def get_books():
    strategy = request.args.get("strategy", "offset").lower()
    genre = request.args.get("genre", "").strip()
    raw_sort = request.args.get("sort", "id")

    if strategy not in ("offset", "cursor"):
        return jsonify({
            "error": "Invalid strategy",
            "detail": "Use strategy=offset or strategy=cursor."
        }), 400

    try:
        sort_keys = parse_sort(raw_sort)
    except ValueError as error:
        return jsonify({
            "error": "Invalid sort",
            "detail": str(error)
        }), 400

    query = Book.query

    if genre:
        query = query.filter(
            Book.category.has(
                or_(
                    Category.slug == genre,
                    func.lower(Category.name) == genre.lower()
                )
            )
        )

    if strategy == "offset":
        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 10))
        except ValueError:
            return jsonify({
                "error": "page and per_page must be integers."
            }), 400

        if page < 1 or not 1 <= per_page <= 100:
            return jsonify({
                "error": "page must be >= 1 and per_page must be 1..100."
            }), 400

        total = query.count()
        query = apply_sort(query, sort_keys)

        books = query.offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        return jsonify({
            "items": [book.to_dict() for book in books],
            "pagination": {
                "strategy": "offset",
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }), 200

    try:
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return jsonify({
            "error": "per_page must be an integer."
        }), 400

    if not 1 <= per_page <= 100:
        return jsonify({
            "error": "per_page must be between 1 and 100."
        }), 400

    token = request.args.get("cursor")

    if token:
        try:
            cursor_data = decode_cursor(token)

            expected_sort = [
                [field, descending]
                for field, descending in sort_keys
            ]

            if cursor_data["sort"] != expected_sort:
                raise ValueError(
                    "Cursor does not match the requested sort."
                )

            query = apply_cursor_filter(
                query,
                sort_keys,
                cursor_data["values"]
            )

        except (ValueError, TypeError, KeyError,
                json.JSONDecodeError, UnicodeDecodeError,
                base64.binascii.Error):
            return jsonify({
                "error": "Invalid cursor",
                "detail": "Provide a valid cursor for the selected sort."
            }), 400

    query = apply_sort(query, sort_keys)
    results = query.limit(per_page + 1).all()

    has_more = len(results) > per_page
    books = results[:per_page]

    next_cursor = None

    if has_more and books:
        last_book = books[-1]

        next_cursor = encode_cursor({
            "sort": [
                [field, descending]
                for field, descending in sort_keys
            ],
            "values": [
                getattr(last_book, field)
                for field, _ in sort_keys
            ]
        })

    return jsonify({
        "items": [book.to_dict() for book in books],
        "pagination": {
            "strategy": "cursor",
            "per_page": per_page,
            "next_cursor": next_cursor,
            "has_more": has_more
        }
    }), 200

@books_bp.get("/<int:book_id>")
def get_book(book_id):
    book = db.session.get(Book, book_id)

    if book is None:
        return jsonify({"error": "Book not found"}), 404

    return jsonify(book.to_dict()), 200

@books_bp.post("")
def create_book():
    data = request.get_json(silent=True)

    error = validate_book(data)
    if error:
        return jsonify({"error": "Invalid book data", "detail": error}), 400

    book = Book(
        title=data["title"].strip(),
        isbn=data["isbn"].strip(),
        price_vnd=data.get("price_vnd", 0),
        stock=data.get("stock", 0),
        category_id=data.get("category_id")
    )

    if not book.title or not book.isbn:
        return jsonify({
            "error": "Invalid book data",
            "detail": "Title and ISBN must not be empty."
        }), 400

    db.session.add(book)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not create book"}), 400

    return jsonify(book.to_dict()), 201

@books_bp.patch("/<int:book_id>")
def update_book(book_id):
    book = db.session.get(Book, book_id)

    if book is None:
        return jsonify({"error": "Book not found"}), 404

    data = request.get_json(silent=True)

    error = validate_book(data, partial=True)
    if error:
        return jsonify({"error": "Invalid book data", "detail": error}), 400

    for field in ("title", "isbn", "price_vnd", "stock", "category_id"):
        if field in data:
            value = data[field]

            if field in ("title", "isbn"):
                value = value.strip()
                if not value:
                    return jsonify({
                        "error": "Invalid book data",
                        "detail": f"{field} must not be empty."
                    }), 400

            setattr(book, field, value)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not update book"}), 400

    return jsonify(book.to_dict()), 200

@books_bp.delete("/<int:book_id>")
def delete_book(book_id):
    book = db.session.get(Book, book_id)

    if book is None:
        return jsonify({"error": "Book not found"}), 404

    db.session.delete(book)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not delete book"}), 400

    return "", 204