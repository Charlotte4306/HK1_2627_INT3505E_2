from flask import Flask, jsonify

app = Flask(__name__)

ORDERS = {
    "ord_01": {
        "id": "11",
        "status": "shipped"
    },
    "ord_02": {
        "id": "12",
        "status": "delivered"
    },
    "ord_03": {
            "id": "13",
            "status": "pending"
        }
}

@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return {"error":"not found"}, 404
    if order["status"] in ("shipped", "delivered"):
        return {"error":"cannot delete"}, 409
    ORDERS.pop(order_id, None)
    return "", 204

if __name__ == "__main__":
    app.run(port=5000, debug=True)