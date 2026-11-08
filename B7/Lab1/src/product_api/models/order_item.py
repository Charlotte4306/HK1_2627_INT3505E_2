from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db

if TYPE_CHECKING:
    from .order import Order
    from .product import Product
    
class OrderItem(db.Model):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "product_id",
            name="uq_order_items_order_product",
        ),
        CheckConstraint(
            "qty > 0",
            name="ck_order_items_qty_positive",
        ),
        CheckConstraint(
            "unit_price_cents >= 0",
            name="ck_order_items_price_nonnegative",
        ),
    )
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        index=True,
        nullable=False,
    )
    
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        index=True,
        nullable=False,
    )
    
    qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    unit_price_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="items",
    )
    
    product: Mapped["Product"] = relationship(
        "Product",
    )