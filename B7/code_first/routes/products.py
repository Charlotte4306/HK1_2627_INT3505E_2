from flask_smorest import Blueprint
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

if __package__ == "code_first.routes":
    from ..models import Product, db
    from ..schemas import ProductErrorSchema, ProductInSchema, ProductSchema
else:
    from models import Product, db
    from schemas import ProductErrorSchema, ProductInSchema, ProductSchema

bp = Blueprint("products", __name__, url_prefix="/products")


# Lấy danh sách sản phẩm
@bp.get("", strict_slashes=False)
@bp.response(200, ProductSchema(many=True))
def list_products():
    rows = db.session.scalars(select(Product).order_by(Product.id)).all()
    return rows


# Tạo sản phẩm từ body JSON, flask-smorest validate theo schema
@bp.post("", strict_slashes=False)
@bp.arguments(ProductInSchema)
@bp.response(201, ProductSchema)
@bp.alt_response(409, schema=ProductErrorSchema, description="SKU đã tồn tại")
def create_product(payload):
    product = Product(**payload)
    db.session.add(product)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "sku already exists"}, 409
    return product
