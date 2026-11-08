from marshmallow import Schema, fields, validate

#Body tạo sản phẩm
class ProductInSchema(Schema):
    sku = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=32),
    )
    
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=255),
            validate.Regexp(r"\S"),
        ],
    )
    
    description = fields.Str(
        allow_none=True,
        validate=validate.Length(max=2000),
    )
    
    price_cents = fields.Int(
        required=True,
        strict=True,
        validate=validate.Range(min=0),
    )
    
    qty_in_stock = fields.Int(
        strict=True,
        load_default=0,
        validate=validate.Range(min=0),
    )
    
#Body cập nhật một phần
class ProductPatchSchema(ProductInSchema):
    pass

# Body đặt trước sản phẩm
class ReserveInSchema(Schema):
    qty = fields.Int(
        required=True,
        strict=True,
        validate=validate.Range(min=1),
    )
    
# Dữ liệu sản phẩm trả về
class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    
# Query string phân trang
class PaginationSchema(Schema):
    page = fields.Int(
        load_default=1,
        validate=validate.Range(min=1),
    )
    
    size = fields.Int(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    
# Response danh sách có phân trang
class ProductPageSchema(Schema):
    items = fields.List(fields.Nested(ProductSchema))
    page = fields.Int()
    size = fields.Int()
    total = fields.Int()
    