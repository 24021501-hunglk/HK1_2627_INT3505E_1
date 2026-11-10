from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from app.schemas.order_item import OrderItemIn, OrderItemOut

class OrderCreateIn(Schema):
    items = fields.List(
        fields.Nested(OrderItemIn),
        required=True,
        validate=validate.Length(min=1)
    )

    @validates_schema
    def validate_duplicate_products(self, data, **kwargs):
        product_ids = [
            item["product_id"] for item in data["items"]
        ]

        if len(product_ids) != len(set(product_ids)):
            raise ValidationError(
                "A product can only appear once in an order."
            )

class OrderItemCreateIn(OrderItemIn):
    pass

class OrderOut(Schema):
    id = fields.Int(dump_only=True)
    status = fields.Str()
    created_at = fields.DateTime()
    items = fields.Nested(OrderItemOut, many=True)