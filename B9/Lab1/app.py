from datetime import date
from os import getenv

from flask import Flask
from werkzeug.http import http_date

from blueprints.v1 import bp as v1_bp
from blueprints.v2 import bp as v2_bp

app = Flask(__name__)
app.json.ensure_ascii = False
app.config["V1_SUNSET"] = http_date(
    date.fromisoformat(getenv("LAB1_V1_SUNSET_DATE", "2027-01-01"))
)

app.register_blueprint(v1_bp, url_prefix="/api/v1/users")
app.register_blueprint(v2_bp, url_prefix="/api/v2/users")

if __name__ == "__main__":
    app.run(port=5000)
