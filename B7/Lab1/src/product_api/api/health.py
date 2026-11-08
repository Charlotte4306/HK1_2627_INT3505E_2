from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db

bp = Blueprint("health", __name__)

# Liveness: ứng dụng còn xử lý request được không
@bp.get("/healthz")
def liveness():
    return jsonify({
        "status": "ok",
    }), 200
    
# Readiness: ứng dụng có kết nối được database không
@bp.get("/ready")
def readliness():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "status": "ok",
            "checks": {
                "db": "ok"
            },
        }), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "status": "degraded",
            "checks": {
                "db": "error",
            },
        }), 503