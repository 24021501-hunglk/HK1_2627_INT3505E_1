from datetime import datetime, timezone

from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    sku: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True
    )

    price_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    qty_in_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product"    
    )

    def __repr__(self):
        return f"<Product id={self.id} sku={self.sku}>"
