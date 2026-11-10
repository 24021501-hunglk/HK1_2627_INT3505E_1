from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)

class ProductOut(Schema):
    """Schema for returning product information."""

    id = fields.Int(dump_only=True)

    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)

    price_cents = fields.Int()
    qty_in_stock = fields.Int()

    archived = fields.Bool()
    created_at = fields.DateTime()

class ProductIn(Schema):
    """Schema for creating a new product."""

    sku = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=32)
    )

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255)
    )

    description = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=2000)
    )

    price_cents = fields.Int(
        required=True,
        validate=validate.Range(min=0)
    )

    qty_in_stock = fields.Int(
        load_default=0,
        validate=validate.Range(min=0)
    )

class ProductPatch(Schema):
    """Schema for partially updating a product."""

    sku = fields.Str(
        validate=validate.Length(min=3, max=32)
    )

    name = fields.Str(
        validate=validate.Length(min=1, max=255)
    )

    description = fields.Str(
        allow_none=True,
        validate=validate.Length(max=2000)
    )

    price_cents = fields.Int(
        validate=validate.Range(min=0)
    )

    qty_in_stock = fields.Int(
        validate=validate.Range(min=0)
    )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one field must be provided."
            )

class ReserveIn(Schema):
    """Schema for reserving product stock."""

    qty = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
