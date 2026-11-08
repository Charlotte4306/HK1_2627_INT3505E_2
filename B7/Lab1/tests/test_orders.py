import pytest

from sqlalchemy import event, func, select

from product_api.extensions import db
from product_api.models import Order, OrderItem, Product


# Hai sản phẩm dùng cho test tạo đơn
@pytest.fixture
def sample_products(app):
    with app.app_context():
        mouse = Product(
            sku="TEST-MOUSE",
            name="Chuột",
            price_cents=25000,
            qty_in_stock=5,
        )

        headset = Product(
            sku="TEST-HEADSET",
            name="Tai nghe",
            price_cents=45000,
            qty_in_stock=3,
        )

        db.session.add_all([mouse, headset])
        db.session.commit()

        return mouse.id, headset.id


# POST thành công phải lưu đơn, các dòng hàng và giảm kho
def test_create_order(app, client, sample_products):
    mouse_id, headset_id = sample_products

    response = client.post(
        "/api/v1/orders",
        json={
            "items": [
                {
                    "product_id": mouse_id,
                    "qty": 2,
                },
                {
                    "product_id": headset_id,
                    "qty": 1,
                },
            ]
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["id"] > 0
    assert data["created_at"]
    assert len(data["items"]) == 2

    items = {
        item["product_id"]: item
        for item in data["items"]
    }

    assert items[mouse_id]["qty"] == 2
    assert items[mouse_id]["unit_price_cents"] == 25000
    assert items[mouse_id]["product"]["sku"] == "TEST-MOUSE"

    assert items[headset_id]["qty"] == 1
    assert items[headset_id]["unit_price_cents"] == 45000

    # Kiểm tra dữ liệu đã được lưu trong database
    with app.app_context():
        order = db.session.get(Order, data["id"])

        assert order is not None
        assert len(order.items) == 2

        assert db.session.get(Product, mouse_id).qty_in_stock == 3
        assert db.session.get(Product, headset_id).qty_in_stock == 2


# Một mặt hàng thiếu kho phải rollback toàn bộ đơn
def test_create_order_rolls_back(
    app,
    client,
    sample_products,
):
    mouse_id, headset_id = sample_products

    response = client.post(
        "/api/v1/orders",
        json={
            "items": [
                {
                    "product_id": mouse_id,
                    "qty": 2,
                },
                {
                    "product_id": headset_id,
                    "qty": 4,
                },
            ]
        },
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "out_of_stock"

    with app.app_context():
        assert db.session.get(Product, mouse_id).qty_in_stock == 5
        assert db.session.get(Product, headset_id).qty_in_stock == 3

        order_count = db.session.scalar(
            select(func.count()).select_from(Order)
        )

        item_count = db.session.scalar(
            select(func.count()).select_from(OrderItem)
        )

        assert order_count == 0
        assert item_count == 0


# GET phải trả đủ dữ liệu và dùng eager loading
def test_list_orders_uses_eager_loading(app, client):
    with app.app_context():
        for index in range(5):
            product = Product(
                sku=f"GET-PRODUCT-{index}",
                name=f"Product {index}",
                price_cents=10000 + index,
                qty_in_stock=10,
            )

            order = Order(
                items=[
                    OrderItem(
                        product=product,
                        qty=1,
                        unit_price_cents=10000 + index,
                    )
                ]
            )

            db.session.add(order)

        db.session.commit()
        db.session.remove()

        engine = db.engine

    select_queries = []

    def count_select(
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ):
        if statement.lstrip().upper().startswith("SELECT"):
            select_queries.append(statement)

    event.listen(
        engine,
        "before_cursor_execute",
        count_select,
    )

    try:
        response = client.get("/api/v1/orders")
    finally:
        event.remove(
            engine,
            "before_cursor_execute",
            count_select,
        )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 5

    for index, order in enumerate(data):
        assert len(order["items"]) == 1

        item = order["items"][0]

        assert item["qty"] == 1
        assert item["unit_price_cents"] == 10000 + index
        assert item["product"]["sku"] == f"GET-PRODUCT-{index}"
        assert item["product"]["name"] == f"Product {index}"

    # Với bộ dữ liệu nhỏ này:
    # 1 SELECT orders
    # 1 SELECT order_items
    # 1 SELECT products
    assert len(select_queries) == 3