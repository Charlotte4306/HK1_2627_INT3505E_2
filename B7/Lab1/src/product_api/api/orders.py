from flask_smorest import Blueprint
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..errors import ApiError
from ..extensions import db
from ..models import Order, OrderItem
from ..services.stock import reserve_stock
from .schemas import OrderInSchema, OrderSchema

bp = Blueprint(
    "orders",
    __name__,
    url_prefix="/api/v1/orders",
)

# Nạp trước các dòng hàng và sản phẩm liên quan
def order_load_options():
    return (
        selectinload(Order.items)
        .selectinload(OrderItem.product)
    )
    
# POST /api/v1/orders
@bp.post("", strict_slashes=False)
@bp.arguments(OrderInSchema)
@bp.response(201, OrderSchema)
def create_order(payload):
    order = Order()
    db.session.add(order)
    # Xử lý sản phẩm theo cùng thứ tự ID
    items = sorted(
        payload["items"],
        key=lambda item: item["product_id"],
    )
    for item in items:
        product = reserve_stock(
            item["product_id"],
            item["qty"],
        )
        order.items.append(
            OrderItem(
                product_id=product.id,
                qty=item["qty"],
                unit_price_cents=product.price_cents,
            )
        )
    # Lấy ID trước khi commit
    db.session.flush()
    order_id = order.id
    db.session.commit()
    return db.session.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(order_load_options())
    )
    
# GET /api/v1/orders
@bp.get("", strict_slashes=False)
@bp.response(200, OrderSchema(many=True))
def list_orders():
    return db.session.scalars(
        select(Order)
        .options(order_load_options())
        .order_by(Order.id)
    ).all()
    
# GET /api/v1/orders/<id>
@bp.get("/<int:order_id>")
@bp.response(200, OrderSchema)
def get_order(order_id):
    order = db.session.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(order_load_options())
    )
    if order is None:
        raise ApiError(
            "not_found",
            "Order not found.",
            404,
        )
    return order