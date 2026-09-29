from flask import Flask, jsonify, request

#Dùng để mã hóa/giải mã cursor thành Base64 url-safe
from base64 import urlsafe_b64decode, urlsafe_b64encode
import json

app = Flask(__name__)

ORDERS = [
    {"id": 1, "status": "paid", "customer_id": 101, "total": 120},
    {"id": 2, "status": "pending", "customer_id": 102, "total": 80},
    {"id": 3, "status": "paid", "customer_id": 101, "total": 250},
    {"id": 4, "status": "cancelled", "customer_id": 103, "total": 60},
    {"id": 5, "status": "paid", "customer_id": 104, "total": 180},
    {"id": 6, "status": "pending", "customer_id": 102, "total": 95},
    {"id": 7, "status": "paid", "customer_id": 105, "total": 310},
]

#Exception riêng cho cursor không hợp lệ
class InvalidCursor(Exception):
    pass

#Mã hóa order_id thành cursor
def encode_cursor(order_id):
    #Tạo Json
    payload = json.dumps({"id": order_id}).encode("utf-8")
    #Mã hóa JSON thành Base64 url-safe
    return urlsafe_b64encode(payload).decode("utf-8")

#Giải mã cursor thành order_id
def decode_cursor(cursor):
    try:
        payload = urlsafe_b64decode(cursor.encode("utf-8"))
        data = json.loads(payload.decode("utf-8"))
        
        if not isinstance(data, dict) or not isinstance(data.get("id"), int):
            raise InvalidCursor
        return data["id"]
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise InvalidCursor
    
#Tạo response lỗi theo format thống nhất
def error_response(detail):
    return jsonify({
        "type": "about:blank",
        "title": "Invalid Request",
        "status": 400,
        "detail": detail,
        "instance": request.path
    }), 400
    
#Lấy danh sách orders
@app.get("/orders")
def list_orders():
    status = request.args.get("status")
    customer_id = request.args.get("customer_id")
    cursor = request.args.get("cursor")
    limit_text = request.args.get("limit", "5")
    sort = request.args.get("sort", "id")
    fields_text = request.args.get("fields")
    
    try:
        limit = int(limit_text)
    except ValueError:
        return error_response("limit must be an integer")
    
    if limit < 1 or limit > 100:
        return error_response("limit must be between 1 and 100")
    
    if sort not in {"id", "total"}:
        return error_response("sort must be id or total")
    
    orders = ORDERS.copy()
    
    #filter theo status
    if status:
        orders = [order for order in orders if order["status"] == status]
        
    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            return error_response("customer_id must be an integer")
        
        orders = [
            order for order in orders
            if order["customer_id"] == customer_id
        ]
        
    #sort theo id
    if sort == "id":
        orders.sort(key=lambda order: order["id"])
    #sort theo total, nếu total = nhau thì sort theo id
    else:
        orders.sort(key=lambda order: (order["total"], order["id"]))
    
    #Nếu client gửi cursor thì thực hiện cursor pagination
    if cursor:
        try:
            cursor_id = decode_cursor(cursor)
        except InvalidCursor:
            return error_response("cursor is invalid")
        
        if sort != "id":
            return error_response("cursor requires sort=id")
        orders = [order for order in orders if order["id"] > cursor_id]
        
    #Lấy thêm 1 record để kiểm tra còn trang tiếp theo hay không
    page = orders[:limit + 1]
    has_more = len(page) > limit
    page = page[:limit]
    
    next_cursor = None
    #Nếu còn dữ liệu -> tạo cursor cho request tiếp theo
    if has_more:
        next_cursor = encode_cursor(page[-1]["id"])
        
    #Nếu client yêu cầu fields cụ thể
    if fields_text:
        fields = [field.strip() for field in fields_text.split(",")]
        #Các field được phép trả về
        allowed_fields = {"id", "status", "customer_id", "total"}
        #tìm field không hợp lệ
        invalid_fields = [field for field in fields if field not in allowed_fields]
        
        if invalid_fields:
            return error_response(
                "unknown fields: " + ",".join(invalid_fields)
            )
        
        #chỉ giữ lại những field client yêu cầu
        page = [
            {field: order[field] for field in fields}
            for order in page
        ]
        
    #trả response thành công
    return jsonify({
        "data": page,
        "page": {
            "limit": limit,
            "has_more": has_more,
            "next_cursor": next_cursor
        }
    }), 200
        
        
if __name__ == "__main__":
    app.run(port=5000, debug=True)
    