from marshmallow import (
    Schema, 
    ValidationError,
    fields, 
    validate,
    validates_schema,
)

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
    
# Một dòng hàng trong body tạo đơn
class OrderItemInSchema(Schema):
    product_id = fields.Int(
        required=True,
        strict=True,
        validate=validate.Range(min=1),
    )
    
    qty = fields.Int(
        required=True,
        strict=True,
        validate=validate.Range(min=1),
    )
    
# Body tạo đơn hàng
class OrderInSchema(Schema):
    items = fields.List(
        fields.Nested(OrderItemInSchema),
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    @validates_schema
    def validate_unique_products(self, data, **kwargs):
        product_ids = [
            item["product_id"]
            for item in data["items"]
        ]
        if len(product_ids) != len(set(product_ids)):
            raise ValidationError({
                "items": [
                    "Each product must appear only once."
                ]
            })
            
# Dữ liệu một dòng hàng trả về
class OrderItemSchema(Schema):
    id = fields.Int()
    product_id = fields.Int()
    qty = fields.Int()
    unit_price_cents = fields.Int()
    product = fields.Nested(
        ProductSchema,
        only=("id", "sku", "name"),
    )
    
# Dữ liệu đơn hàng trả về
class OrderSchema(Schema):
    id = fields.Int()
    created_at = fields.DateTime()
    items = fields.List(
        fields.Nested(OrderItemSchema)
    )