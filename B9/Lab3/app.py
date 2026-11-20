from datetime import datetime
from os import getenv

from flask import Flask

from sunset import deprecate_at

app = Flask(__name__)
app.json.ensure_ascii = False

V1_SUNSET = datetime.fromisoformat(
    getenv("LAB3_V1_SUNSET", "2026-12-31T23:59:59+00:00")
)
USERS = {1: {"first_name": "Văn", "last_name": "Nguyễn"}}


@app.get("/api/v1/users/<int:uid>")
@deprecate_at(V1_SUNSET, replacement="/api/v2/users")
def get_v1(uid):
    user = USERS.get(uid)
    if user is None:
        return {"error": "nf"}, 404
    return {"id": uid, "full_name": f"{user['first_name']} {user['last_name']}"}


@app.get("/api/v2/users")
def list_v2():
    return [{"id": uid, **user} for uid, user in USERS.items()]


if __name__ == "__main__":
    app.run(port=5000)
