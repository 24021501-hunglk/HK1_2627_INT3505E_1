from sqlalchemy import (
    Integer,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

class OrderItem(db.Model):
    __tablename__ = "order_items"

    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "product_id",
            name="uq_order_product"
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_order_item_quantity"
        ),
        CheckConstraint(
            "unit_price_cents >= 0",
            name="ck_order_item_price"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    unit_price_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    order: Mapped["Order"] = relationship(
        back_populates="items"
    )

    product: Mapped["Product"] = relationship(
        back_populates="order_items"
    )

    def __repr__(self):
        return (
            f"<OrderItem order_id={self.order_id} "
            f"product_id={self.product_id}>"
        )