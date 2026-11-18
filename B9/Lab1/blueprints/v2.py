import re

from flask import Blueprint, request, url_for

from .users_data import create_user, get_user

bp = Blueprint("v2", __name__)
USER_FIELDS = ("first_name", "last_name", "email")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@bp.post("")
def create():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.keys() != set(USER_FIELDS):
        return {"error": "Expected first_name, last_name and email"}, 400

    values = {}
    for field in USER_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            return {"error": f"{field} must be a non-empty string"}, 400
        values[field] = value.strip()

    if not EMAIL_PATTERN.fullmatch(values["email"]):
        return {"error": "email must be a valid email address"}, 400

    uid, user = create_user(**values)
    return {"id": uid, **user}, 201, {"Location": url_for(".get", uid=uid)}


@bp.get("/<int:uid>")
def get(uid):
    user = get_user(uid)
    if user is None:
        return {"error": "nf"}, 404

    return {"id": uid, **user}
