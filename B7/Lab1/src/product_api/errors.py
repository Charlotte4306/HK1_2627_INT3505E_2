import json 

from flask import jsonify
from werkzeug.exceptions import HTTPException

from .extensions import db

class ApiError(Exception):
    def __init__(self, error, detail, status_code):
        super().__init__(detail)
        self.error = error
        self.detail = detail
        self.status_code = status_code
        
def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        db.session.rollback()
        return jsonify({
            "error": err.error,
            "detail": err.detail,
        }), err.status_code
        
    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        db.session.rollback()
        data = getattr(err, "data", None) or {}
        detail = data.get("errors") or data.get("message")
        if detail is None:
            detail = err.description
        if not isinstance(detail, str):
            detail = json.dumps(detail, ensure_ascii=False)
        response = err.get_response()
        response.set_data(app.json.dumps({
            "error": err.name.lower().replace(" ", "_"),
            "detail": detail,
        }))
        response.content_type = "application/json"
        return response
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        db.session.rollback()
        app.logger.exception("Unhandled error")
        return jsonify({
            "error": "internal_error",
            "detail": "An unexpected error occurred",
        }), 500
        
