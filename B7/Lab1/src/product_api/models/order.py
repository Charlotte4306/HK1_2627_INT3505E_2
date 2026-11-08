from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db

if TYPE_CHECKING:
    from .order_item import OrderItem
    
class Order(db.Model):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.id",
    )
    