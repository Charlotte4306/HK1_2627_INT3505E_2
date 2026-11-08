from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import mapped_column

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price_cents >= 0"),)

    id = mapped_column(Integer, primary_key=True)
    sku = mapped_column(String(32), unique=True, nullable=False)
    name = mapped_column(String(255), nullable=False)
    price_cents = mapped_column(Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "price_cents": self.price_cents,
        }
