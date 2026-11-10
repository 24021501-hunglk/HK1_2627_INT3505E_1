from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import (
    OrderCreateIn,
    OrderItemCreateIn,
    OrderOut,
)

orders_bp = Blueprint("orders", __name__)

order_create_schema = OrderCreateIn()
order_item_create_schema = OrderItemCreateIn()
order_out_schema = OrderOut()

def error_response(status_code, error, detail):
    return jsonify({
        "error": error,
        "detail": detail
    }), status_code

def get_order(order_id):
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    return db.session.scalar(stmt)

@orders_bp.post("")
def create_order():
    json_data = request.get_json(silent=True)

    if not isinstance(json_data, dict):
        return error_response(
            422,
            "ValidationError",
            "Request body must be a JSON object."
        )

    try:
        data = order_create_schema.load(json_data)
    except ValidationError as exc:
        return jsonify({
            "error": "ValidationError",
            "detail": exc.messages
        }), 422

    product_ids = [
        item["product_id"] for item in data["items"]
    ]

    products = db.session.scalars(
        select(Product).where(
            Product.id.in_(product_ids),
            Product.archived.is_(False)
        )
    ).all()

    product_map = {
        product.id: product for product in products
    }

    missing_ids = [
        product_id
        for product_id in product_ids
        if product_id not in product_map
    ]

    if missing_ids:
        return error_response(
            404,
            "NotFound",
            f"Products not found or archived: {missing_ids}"
        )

    order = Order(status="pending")

    try:
        db.session.add(order)
        db.session.flush()

        for item_data in data["items"]:
            product = product_map[item_data["product_id"]]

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_data["quantity"],
                unit_price_cents=product.price_cents
            )

            db.session.add(order_item)

        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return error_response(
            409,
            "Conflict",
            "Could not create order due to a database conflict."
        )

    return jsonify(order_out_schema.dump(order)), 201

@orders_bp.get("")
def list_orders():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    if page < 1 or per_page < 1 or per_page > 100:
        return error_response(
            422,
            "ValidationError",
            "page must be >= 1 and per_page must be between 1 and 100."
        )

    count_stmt = select(db.func.count(Order.id))
    total = db.session.scalar(count_stmt)

    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.id)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    orders = db.session.scalars(stmt).all()

    return jsonify({
        "items": order_out_schema.dump(orders, many=True),
        "page": page,
        "per_page": per_page,
        "total": total
    }), 200

@orders_bp.get("/<int:order_id>")
def get_order_detail(order_id):
    order = get_order(order_id)

    if order is None:
        return error_response(
            404,
            "NotFound",
            "Order not found."
        )

    return jsonify(order_out_schema.dump(order)), 200

@orders_bp.post("/<int:order_id>/items")
def add_order_item(order_id):
    order = get_order(order_id)

    if order is None:
        return error_response(
            404,
            "NotFound",
            "Order not found."
        )

    json_data = request.get_json(silent=True)

    if not isinstance(json_data, dict):
        return error_response(
            422,
            "ValidationError",
            "Request body must be a JSON object."
        )

    try:
        data = order_item_create_schema.load(json_data)
    except ValidationError as exc:
        return jsonify({
            "error": "ValidationError",
            "detail": exc.messages
        }), 422

    product = db.session.scalar(
        select(Product).where(
            Product.id == data["product_id"],
            Product.archived.is_(False)
        )
    )

    if product is None:
        return error_response(
            404,
            "NotFound",
            "Product not found or archived."
        )

    existing_item = db.session.scalar(
        select(OrderItem).where(
            OrderItem.order_id == order_id,
            OrderItem.product_id == product.id
        )
    )

    if existing_item is not None:
        return error_response(
            409,
            "Conflict",
            "Product already exists in this order."
        )

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=data["quantity"],
        unit_price_cents=product.price_cents
    )

    try:
        db.session.add(order_item)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response(
            409,
            "Conflict",
            "Could not add order item."
        )

    return jsonify(order_out_schema.dump(get_order(order_id))), 201