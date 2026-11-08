from flask_smorest import Blueprint
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..errors import ApiError
from ..extensions import db
from ..models import Product
from ..services.stock import reserve_stock

from .schemas import (
    PaginationSchema,
    ProductInSchema,
    ProductPageSchema,
    ProductPatchSchema,
    ProductSchema,
    ReserveInSchema,
)

bp = Blueprint(
    "products",
    __name__,
    url_prefix="/api/v1/products",
)

# Tìm sản phẩm chưa bị xóa 
def get_active_product(product_id):
    product = db.session.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.archived.is_(False),
        )
    )
    if product is None:
        raise ApiError(
            "not_found",
            "Product not found.",
            404,
        )
    return product

# Kiểm tra SKU trùng, kể cả sản phẩm đã archive
def check_sku(sku, product_id=None):
    stmt = select(Product.id).where(Product.sku == sku)
    if product_id is not None:
        stmt = stmt.where(Product.id != product_id)
    if db.session.scalar(stmt) is not None:
        raise ApiError(
            "conflict",
            "SKU already exists.",
            409,
        )
        
#xử lý trường hợp SKU trùng do request đồng thời
def save_product(product):
    sku = product.sku
    product_id = product.id
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        check_sku(sku, product_id)
        raise

# GET /api/v1/products?page=1&size=20
@bp.get("", strict_slashes=False)
@bp.arguments(PaginationSchema, location="query")
@bp.response(200, ProductPageSchema)
def list_products(query):
    page = query["page"]
    size = query["size"]
    rows = db.session.scalars(
        select(Product)
        .where(Product.archived.is_(False))
        .order_by(Product.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    total = db.session.scalar(
        select(func.count())
        .select_from(Product)
        .where(Product.archived.is_(False))
    )
    
    return {
        "items": rows,
        "page": page,
        "size": size,
        "total": total,
    }
    
# GET /api/v1/products/<id>
@bp.get("/<int:product_id>")
@bp.response(200, ProductSchema)
def get_product(product_id):
    return get_active_product(product_id)   
    
# POST /api/v1/products
@bp.post("",strict_slashes=False)
@bp.arguments(ProductInSchema)
@bp.response(201, ProductSchema)
def create_product(payload):
    check_sku(payload["sku"])
    product = Product(**payload)
    db.session.add(product)
    save_product(product)
    return product

# POST /api/v1/products/<id>/reserve
@bp.post("/<int:product_id>/reserve")
@bp.arguments(ReserveInSchema)
@bp.response(200, ProductSchema)
def reserve_product(payload, product_id):
    product = reserve_stock(
        product_id,
        payload["qty"],
    )
    db.session.commit()
    return product

# PATCH /api/v1/products/<id>
@bp.patch("/<int:product_id>")
@bp.arguments(ProductPatchSchema(partial=True))
@bp.response(200, ProductSchema)
def patch_product(payload, product_id):
    product = get_active_product(product_id)
    if "sku" in payload:
        check_sku(payload["sku"], product_id)
        
    for key, value in payload.items():
        setattr(product, key, value)
        
    save_product(product)
    return product

# DELETE /api/v1/products/<id>
@bp.delete("/<int:product_id>")
@bp.response(204)
def delete_product(product_id):
    product = get_active_product(product_id)
    product.archived = True
    
    db.session.commit()
    return None