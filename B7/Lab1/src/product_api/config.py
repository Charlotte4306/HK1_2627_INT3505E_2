import os

class DefaultConfig:
    # Cấu hình database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DB_URL",
        "sqlite:///products.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Thông tin tài liệu OpenAPI
    API_TITLE = "Product API - Lab 1"
    API_VERSION = "1.0.0"
    OPENAPI_VERSION = "3.0.3"
    # Đường dẫn truy cập tài liệu API
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_JSON_PATH = "openapi.json"
    OPENAPI_SWAGGER_UI_PATH = "/docs/"
    OPENAPI_SWAGGER_UI_URL = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/"
    )