import os

from flask import Flask
from flask_smorest import Api

if __package__:
    from .models import db
    from .routes.products import bp as products_bp
else:
    from models import db
    from routes.products import bp as products_bp


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URL", "sqlite:///code_first.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.ensure_ascii = False

# Cấu hình để flask-smorest sinh OpenAPI và hiển thị Swagger UI
app.config["API_TITLE"] = "Product API - Code First"
app.config["API_VERSION"] = "1.0.0"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_JSON_PATH"] = "openapi.json"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs/"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/"

db.init_app(app)
api = Api(app)
api.register_blueprint(products_bp)

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5001)))
