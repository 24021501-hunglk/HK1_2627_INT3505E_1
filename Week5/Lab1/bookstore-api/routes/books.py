import json
from pathlib import Path

from flask import Blueprint, jsonify, request
from jsonschema import validate, ValidationError

from models import db, Book


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

@books_bp.get("")
def get_books():
    books = Book.query.order_by(Book.id).all()
    return jsonify([book.to_dict() for book in books]), 200


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