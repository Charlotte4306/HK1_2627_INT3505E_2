from marshmallow import Schema, fields, validate


# Schema validate body khi tạo sản phẩm
class ProductInSchema(Schema):
    sku = fields.Str(required=True, validate=[
        validate.Length(min=3, max=32),
        validate.Regexp(r"^[A-Z0-9-]+$"),
    ])
    name = fields.Str(required=True, validate=[
        validate.Length(min=1, max=255), validate.Regexp(r"\S"),
    ])
    price_cents = fields.Int(required=True, strict=True, validate=validate.Range(min=0))


# Schema chuyển model thành JSON và mô tả response trong OpenAPI
class ProductSchema(Schema):
    id = fields.Int(dump_only=True, required=True)
    sku = fields.Str(required=True)
    name = fields.Str(required=True)
    price_cents = fields.Int(required=True)


class ProductErrorSchema(Schema):
    error = fields.Str()
