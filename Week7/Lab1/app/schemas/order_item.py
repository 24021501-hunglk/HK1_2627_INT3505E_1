from marshmallow import Schema, fields, validate

class OrderItemIn(Schema):
    product_id = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )

    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )

class OrderItemOut(Schema):
    id = fields.Int(dump_only=True)
    order_id = fields.Int()
    product_id = fields.Int()
    quantity = fields.Int()
    unit_price_cents = fields.Int()