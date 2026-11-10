from flask import Blueprint, request, jsonify
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.product import Product
from app.schemas.product import (
    ProductOut,
    ProductIn,
    ProductPatch,
    ReserveIn,
)

products_bp = Blueprint("products", __name__)

product_out_schema = ProductOut()
product_in_schema = ProductIn()
product_patch_schema = ProductPatch()
reserve_schema = ReserveIn()


# Helper: create error response
def error_response(status_code, error, detail):
    return jsonify({
        "error": error,
        "detail": detail
    }), status_code


# Helper: find active product
def get_active_product(product_id):
    stmt = select(Product).where(
        Product.id == product_id,
        Product.archived.is_(False)
    )

    return db.session.scalar(stmt)


# 1. GET /api/v1/products
# List products with pagination
@products_bp.get("")
def list_products():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    if page < 1 or per_page < 1 or per_page > 100:
        return error_response(
            422,
            "ValidationError",
            "page must be >= 1 and per_page must be between 1 and 100."
        )

    stmt = select(Product).where(
        Product.archived.is_(False)
    )

    total = db.session.scalar(
        select(db.func.count()).select_from(stmt.subquery())
    )

    products = db.session.scalars(
        stmt.order_by(Product.id)
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()

    return jsonify({
        "items": product_out_schema.dump(products, many=True),
        "page": page,
        "per_page": per_page,
        "total": total
    }), 200


# 2. GET /api/v1/products/<id>
# Get product details
@products_bp.get("/<int:product_id>")
def get_product(product_id):
    product = get_active_product(product_id)

    if product is None:
        return error_response(
            404,
            "NotFound",
            "Product not found."
        )

    return jsonify(product_out_schema.dump(product)), 200


# 3. POST /api/v1/products
# Create product
@products_bp.post("")
def create_product():
    json_data = request.get_json(silent=True)

    if not isinstance(json_data, dict):
        return error_response(
            422,
            "ValidationError",
            "Request body must be a JSON object."
        )

    try:
        data = product_in_schema.load(json_data)
    except Exception as exc:
        from marshmallow import ValidationError

        if isinstance(exc, ValidationError):
            return jsonify({
                "error": "ValidationError",
                "detail": exc.messages
            }), 422
        raise

    product = Product(**data)

    try:
        db.session.add(product)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response(
            409,
            "Conflict",
            "SKU already exists."
        )

    return jsonify(product_out_schema.dump(product)), 201


# 4. POST /api/v1/products/<id>/reserve
# Reserve product stock
@products_bp.post("/<int:product_id>/reserve")
def reserve_product(product_id):
    product = get_active_product(product_id)

    if product is None:
        return error_response(
            404,
            "NotFound",
            "Product not found."
        )

    json_data = request.get_json(silent=True)

    if not isinstance(json_data, dict):
        return error_response(
            422,
            "ValidationError",
            "Request body must be a JSON object."
        )

    from marshmallow import ValidationError

    try:
        data = reserve_schema.load(json_data)
    except ValidationError as exc:
        return jsonify({
            "error": "ValidationError",
            "detail": exc.messages
        }), 422

    if product.qty_in_stock < data["qty"]:
        return error_response(
            409,
            "Conflict",
            "Insufficient stock."
        )

    product.qty_in_stock -= data["qty"]

    db.session.commit()

    return jsonify(product_out_schema.dump(product)), 200


# 5. PATCH /api/v1/products/<id>
# Update product partially
@products_bp.patch("/<int:product_id>")
def update_product(product_id):
    product = get_active_product(product_id)

    if product is None:
        return error_response(
            404,
            "NotFound",
            "Product not found."
        )

    json_data = request.get_json(silent=True)

    if not isinstance(json_data, dict):
        return error_response(
            422,
            "ValidationError",
            "Request body must be a JSON object."
        )

    from marshmallow import ValidationError

    try:
        data = product_patch_schema.load(json_data)
    except ValidationError as exc:
        return jsonify({
            "error": "ValidationError",
            "detail": exc.messages
        }), 422

    if "sku" in data:
        existing = db.session.scalar(
            select(Product).where(
                Product.sku == data["sku"],
                Product.id != product_id
            )
        )

        if existing is not None:
            return error_response(
                409,
                "Conflict",
                "SKU already exists."
            )

    for key, value in data.items():
        setattr(product, key, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response(
            409,
            "Conflict",
            "Product update conflicts with existing data."
        )

    return jsonify(product_out_schema.dump(product)), 200


# 6. DELETE /api/v1/products/<id>
# Soft delete product
@products_bp.delete("/<int:product_id>")
def delete_product(product_id):
    product = get_active_product(product_id)

    if product is None:
        return error_response(
            404,
            "NotFound",
            "Product not found."
        )

    product.archived = True

    db.session.commit()

    return "", 204
