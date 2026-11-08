from flask import Flask
from flask_smorest import Api

from .api.products import bp as products_bp
from .api.orders import bp as orders_bp
from .config import DefaultConfig
from .errors import register_error_handlers
from .extensions import db, migrate

def create_app(config=None):
    app = Flask(__name__)
    # Nạp cấu hình mặc định
    app.config.from_object(DefaultConfig)
    # Cho phép ghi đè cấu hình khi cần
    if config:
        app.config.update(config)
        
    app.json.ensure_ascii = False
    # Gắn extension vào app
    db.init_app(app)
    migrate.init_app(app, db)
    # Khởi tạo OpenAPI và đăng ký Product blueprint
    api = Api(app)
    api.register_blueprint(products_bp)
    api.register_blueprint(orders_bp)
    # Đăng ký sau Api để sử dụng định dạng lỗi của bài
    register_error_handlers(app)
    return app