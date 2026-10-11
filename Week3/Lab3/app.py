from flask import Flask, jsonify, request
import json
import base64
app = Flask(__name__)

ORDERS = [
    {
        "id": 1,
        "customer_id": 101,
        "status": "paid",
        "total": 150000
    },
    {
        "id": 2,
        "customer_id": 102,
        "status": "pending",
        "total": 200000
    },
    {
        "id": 3,
        "customer_id": 101,
        "status": "paid",
        "total": 300000
    },
    {
        "id": 4,
        "customer_id": 103,
        "status": "cancelled",
        "total": 100000
    },
    {
        "id": 5,
        "customer_id": 102,
        "status": "paid",
        "total": 500000
    },
    {
        "id": 6,
        "customer_id": 104,
        "status": "pending",
        "total": 250000
    },
    {
        "id": 7,
        "customer_id": 101,
        "status": "paid",
        "total": 400000
    },
    {
        "id": 8,
        "customer_id": 105,
        "status": "paid",
        "total": 350000
    }
]

def encode_cursor(order):
    data = {
        "value": order["id"],
        "id": order["id"]
    }

    raw = json.dumps(data).encode()

    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor):
    try:
        raw = base64.urlsafe_b64decode(cursor.encode())
        data = json.loads(raw.decode())

        if "value" not in data or "id" not in data:
            raise ValueError

        return data

    except Exception:
        raise ValueError("Invalid cursor")

@app.get("/orders")
def get_orders():
    cursor = request.args.get("cursor")
    status = request.args.get("status")
    customer_id = request.args.get("customer_id")
    sort = request.args.get("sort", "id")
    fields = request.args.get("fields")

    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    if limit <= 0:
        return jsonify({"error": "limit must be greater than 0"}), 400

    orders = ORDERS.copy()

    if status:
        orders = [order for order in orders if order["status"] == status]

    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            return jsonify({"error": "customer_id must be an integer"}), 400

        orders = [order for order in orders if order["customer_id"] == customer_id]

    allowed_sort = {
        "id": ("id", False),
        "-id": ("id", True),
        "total": ("total", False),
        "-total": ("total", True)
    }

    if sort not in allowed_sort:
        return jsonify({"error": "Invalid sort"}), 400

    sort_field, reverse = allowed_sort[sort]

    orders.sort(
        key=lambda order: order[sort_field],
        reverse=reverse
    )

    if cursor:
        try:
            cursor_data = decode_cursor(cursor)

        except ValueError:
            return jsonify({"error": "Invalid cursor"}), 400

        cursor_value = cursor_data["value"]
        cursor_id = cursor_data["id"]

        start_index = None

        for i, order in enumerate(orders):
            current_value = order[sort_field]

            if not reverse:
                if (
                    current_value > cursor_value
                    or (
                        current_value == cursor_value
                        and order["id"] > cursor_id
                    )
                ):
                    start_index = i
                    break

            else:
                if (
                    current_value < cursor_value
                    or (
                        current_value == cursor_value
                        and order["id"] < cursor_id
                    )
                ):
                    start_index = i
                    break


        if start_index is None:
            orders = []

        else:
            orders = orders[start_index:]

    has_next = len(orders) > limit
    page = orders[:limit]
    next_cursor = None

    if has_next and page:
        next_cursor = encode_cursor(page[-1])

    if fields:
        requested_fields = fields.split(",")
        allowed_fields = {
            "id",
            "customer_id",
            "status",
            "total",
            "created_at"
        }

        for field in requested_fields:
            if field not in allowed_fields:
                return jsonify({"error": f"Invalid field: {field}"}), 400

        result = [
            {
                field: order[field]
                for field in requested_fields
            }
            for order in page
        ]

    else:
        result = page

    return jsonify({
        "data": result,
        "next_cursor": next_cursor,
        "has_next": has_next
    })

if __name__ == "__main__":
    app.run(debug=True)