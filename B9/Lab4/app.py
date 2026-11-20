from os import getenv

from flask import Flask, jsonify, request

from gateway import dispatch

app = Flask(__name__)
try:
    percent = int(getenv("V2_PERCENT", "5"))
except ValueError as exc:
    raise ValueError("V2_PERCENT must be an integer from 0 to 100") from exc
if not 0 <= percent <= 100:
    raise ValueError("V2_PERCENT must be an integer from 0 to 100")
app.config["V2_PERCENT"] = percent


@app.post("/orders")
def create_order():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return {"error": "Expected a JSON object"}, 400

    account_id = body.get("account_id")
    if not isinstance(account_id, str) or not account_id.strip():
        return {"error": "account_id must be a non-empty string"}, 400
    body["account_id"] = account_id.strip()

    version, result = dispatch(body)
    response = jsonify(result)
    response.headers["X-Order-Handler"] = version
    return response, 201 if version == "v2" else 200


if __name__ == "__main__":
    app.run(port=5000)
