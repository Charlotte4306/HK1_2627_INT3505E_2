from sqlalchemy import select

from ..errors import ApiError
from ..extensions import db
from ..models import Product

def reserve_stock(product_id, qty):
    table = Product.__table__
    
    stmt = (
        table.update()
        .where(
            table.c.id == product_id,
            table.c.archived.is_(False),
            table.c.qty_in_stock >= qty,
        )
        .values(
                qty_in_stock=table.c.qty_in_stock - qty,
        )
    )
    result = db.session.execute(stmt)
    if result.rowcount != 1:
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
        raise ApiError(
            "out_of_stock",
            f"Only {product.qty_in_stock} item(s) available.",
            409,
        )
        
    product = db.session.scalar(
        select(Product)
        .where(Product.id == product_id)
        .execution_options(populate_existing=True)
    )
    
    return product