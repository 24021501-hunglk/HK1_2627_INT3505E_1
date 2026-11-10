from app.extensions import db
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem

def create_test_product(sku):
    product = Product(
        sku=sku,
        name=f"Test Product {sku}",
        description="Product for pytest",
        price_cents=100000,
        qty_in_stock=100
    )

    db.session.add(product)
    db.session.flush()

    return product

def test_create_order(client, app):
    with app.app_context():
        product = create_test_product("TEST-POST-001")
        product_id = product.id

        db.session.commit()

    response = client.post(
        "/api/v1/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 201
    assert response.is_json

def test_list_orders_avoids_n_plus_one(
    client, app, query_counter
):
    with app.app_context():
        for i in range(5):
            product = create_test_product(f"TEST-GET-{i}")

            order = Order(status="pending")
            db.session.add(order)
            db.session.flush()

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=1,
                unit_price_cents=product.price_cents
            )

            db.session.add(order_item)

        db.session.commit()

    query_counter.clear()

    response = client.get("/api/v1/orders")

    assert response.status_code == 200
    assert response.is_json

    select_count = len(query_counter)

    print(f"\nSố truy vấn SELECT: {select_count}")

    assert select_count <= 3, (
        f"Phát hiện nguy cơ N+1: "
        f"có {select_count} truy vấn SELECT."
    )