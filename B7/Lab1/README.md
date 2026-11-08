# Lab 1 — Product API và Order API

## Cấu trúc thư mục

```text
Lab1/
├── README.md
├── pyproject.toml                  # Thông tin package, dependencies và cấu hình pytest
├── .env.example                    # Cấu hình môi trường mẫu
├── .gitignore
├── .dockerignore
├── Dockerfile                      # Build image nhiều stage, chạy bằng Gunicorn
├── docker-compose.yml              # PostgreSQL, migration và API
├── wsgi.py                         # Điểm khởi chạy ứng dụng
├── migrations/
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── bdf1083e5d89_create_products_table.py
│       └── f88eed695ccb_create_orders_and_order_items.py
├── src/
│   └── product_api/
│       ├── __init__.py
│       ├── config.py                # Cấu hình database và OpenAPI
│       ├── extensions.py            # SQLAlchemy và Flask-Migrate
│       ├── errors.py                # Xử lý lỗi tập trung
│       ├── factory.py               # Application factory, đăng ký blueprint
│       ├── api/
│       │   ├── __init__.py
│       │   ├── products.py          # Sáu endpoint Product
│       │   ├── orders.py            # Tạo và đọc Order
│       │   ├── health.py            # /healthz và /ready
│       │   └── schemas.py           # Validate input và serialize output
│       ├── models/
│       │   ├── __init__.py
│       │   ├── product.py
│       │   ├── order.py
│       │   └── order_item.py
│       └── services/
│           ├── __init__.py
│           └── stock.py             # Giảm kho bằng UPDATE có điều kiện
└── tests/
    ├── conftest.py                  # App, test client và database tạm
    └── test_orders.py               # POST, rollback và GET eager loading
```

## Giới thiệu

Bài thực hành xây dựng backend service bằng Flask theo cấu trúc `src/product_api`, sử dụng application factory, blueprint, SQLAlchemy 2.x và Marshmallow. API chạy trực tiếp với SQLite hoặc chạy trong Docker cùng PostgreSQL.

Các phần đã triển khai:

1. Product API gồm sáu endpoint: danh sách có phân trang, chi tiết, tạo, reserve, cập nhật một phần và xóa mềm.
2. Order và OrderItem liên kết đơn hàng với nhiều sản phẩm, có blueprint riêng `/api/v1/orders`.
3. Dockerfile nhiều stage và Docker Compose cho API, PostgreSQL và migration.
4. Hai endpoint riêng `/healthz` và `/ready`.
5. Pytest cho POST tạo đơn, rollback và GET có eager loading, kèm đếm truy vấn để phát hiện N+1.

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Web framework | Flask |
| API và tài liệu | flask-smorest, OpenAPI 3.0.3, Swagger UI |
| Validation, serialization | Marshmallow |
| ORM | SQLAlchemy 2.0, Flask-SQLAlchemy |
| Migration | Flask-Migrate, Alembic |
| Database | SQLite khi chạy cục bộ; PostgreSQL 16 trong Docker |
| WSGI server trong Docker | Gunicorn, 2 worker |
| Kiểm thử | pytest, Flask test client |

## Chạy bằng Docker Compose

### Chuẩn bị

- Cài Docker Engine và Docker Compose v2; trên Windows có thể dùng Docker Desktop ở chế độ Linux containers.
- Lấy đầy đủ source của repo, bao gồm thư mục `migrations/`.
- Mở Docker Desktop nếu dùng Windows, đợi Engine sẵn sàng.
- Đảm bảo port `5000` chưa được chương trình khác sử dụng.

Không cần cài Python hoặc PostgreSQL trực tiếp trên máy khi chỉ chạy bằng Docker. Lần build đầu cần Internet để tải image và thư viện.

Từ thư mục gốc repo, chuyển đến bài thực hành:

```powershell
cd B7/Lab1
docker compose up --build -d
```

Compose thực hiện theo thứ tự:

```text
PostgreSQL sẵn sàng → Chạy db upgrade → Khởi động API bằng Gunicorn
```

Kiểm tra trạng thái:

```powershell
docker compose ps -a
```

| Service | Trạng thái mong đợi | Vai trò |
|---|---|---|
| `db` | Up, healthy | PostgreSQL |
| `migrate` | Exited (0) | Áp dụng migration rồi kết thúc |
| `api` | Up | Nhận request tại port 5000 |

Truy cập:

- Swagger UI: <http://localhost:5000/docs/>
- OpenAPI JSON: <http://localhost:5000/openapi.json>
- Liveness: <http://localhost:5000/healthz>
- Readiness: <http://localhost:5000/ready>

Hai endpoint health dùng Blueprint thường của Flask nên không tự xuất hiện trong Swagger UI. Gọi chúng trực tiếp bằng trình duyệt hoặc HTTP client.

### Database trong Docker

Compose truyền cấu hình sau cho API và migration:

```text
DB_URL=postgresql+psycopg://app:devpw@db:5432/appdb
```

`db` là hostname của service PostgreSQL trong mạng Compose. Tài khoản `app/devpw` dùng cho thực hành cục bộ. Database chỉ được truy cập trong mạng Compose; không ánh xạ port PostgreSQL ra máy host.

Dữ liệu được lưu trong named volume `pgdata`. Database mới ban đầu trống, không tự sao chép dữ liệu SQLite hoặc dữ liệu từ máy khác khi clone repo.

### Các lệnh thường dùng

Chạy các lệnh dưới đây tại `B7/Lab1`.

```powershell
# Xem log
docker compose logs --tail=100 api migrate db

# Dừng và gỡ container, giữ dữ liệu trong volume
docker compose down

# Chạy lại sau khi dừng
docker compose up -d

# Build lại sau khi sửa source hoặc dependencies
docker compose up --build -d
```

Image hiện tại không bind mount source, vì vậy cần build lại để container nhận code mới. Không dùng `docker compose down -v` nếu muốn giữ dữ liệu: tùy chọn `-v` sẽ xóa volume PostgreSQL của bài.

## Chạy trực tiếp với SQLite

Yêu cầu Python từ 3.10 trở lên. Các lệnh dưới đây dùng PowerShell, chạy tại `B7/Lab1`.

```powershell
# Nếu đã có virtual environment đang kích hoạt thì bỏ qua hai dòng này
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài package theo chế độ editable
python -m pip install -e .

# Áp dụng các migration đã có trong repo
python -m flask --app wsgi:app db upgrade

# Chạy development server
python -m flask --app wsgi:app run --debug
```

Mở <http://127.0.0.1:5000/docs/>. Dừng API Docker trước nếu đang chiếm port `5000`.

Khi không đặt biến môi trường `DB_URL`, ứng dụng dùng `sqlite:///products.db`. File database nằm trong thư mục instance mà Flask xác định cho ứng dụng, không nhất thiết là thư mục đang mở terminal. Có thể xem đường dẫn bằng:

```powershell
python -m flask --app wsgi:app shell
```

Trong Python shell:

```python
from flask import current_app
print(current_app.instance_path)
exit()
```

`.env.example` là file mẫu, không tự được nạp. Project hiện chưa khai báo `python-dotenv`; khi cần đổi database, đặt `DB_URL` trong môi trường trước khi chạy Flask. Các lệnh trên đã chỉ định rõ app và chế độ debug.

## Database và migration

Quan hệ dữ liệu:

```text
Order (1) ─── (N) OrderItem (N) ─── (1) Product
```

- `Product`: SKU duy nhất, tên, mô tả, giá nguyên theo cent, tồn kho, trạng thái archive và thời gian tạo/cập nhật.
- `Order`: thông tin chung của đơn, thời gian tạo và danh sách dòng hàng.
- `OrderItem`: liên kết Order–Product, số lượng và đơn giá tại thời điểm đặt.
- Mỗi Product chỉ xuất hiện một dòng trong cùng Order; mua nhiều thì tăng `qty`.

Các migration hiện có đã được lưu trong repo. Người lấy source về chỉ cần `db upgrade`, không chạy lại `db init` hoặc tự sinh migration mới.

Khi phát triển và thay đổi model, tạo migration mới tại `B7/Lab1`:

```powershell
python -m flask --app wsgi:app db migrate -m "describe model changes"
# Đọc và kiểm tra file vừa sinh trong migrations/versions/
python -m flask --app wsgi:app db upgrade
python -m flask --app wsgi:app db current
```

## Các endpoint

### Product

| Method | Endpoint | Chức năng | Thành công |
|---|---|---|---|
| GET | `/api/v1/products?page=1&size=20` | Danh sách có phân trang | 200 |
| GET | `/api/v1/products/{id}` | Chi tiết sản phẩm chưa archive | 200 |
| POST | `/api/v1/products` | Tạo sản phẩm | 201 |
| POST | `/api/v1/products/{id}/reserve` | Giảm tồn kho theo số lượng yêu cầu | 200 |
| PATCH | `/api/v1/products/{id}` | Cập nhật các trường có trong body | 200 |
| DELETE | `/api/v1/products/{id}` | Xóa mềm bằng `archived=True` | 204 |

Quy tắc dữ liệu:

- `sku`: từ 3–32 ký tự, không trùng kể cả với sản phẩm đã archive.
- `name`: từ 1–255 ký tự, không chỉ chứa khoảng trắng.
- `description`: tùy chọn, tối đa 2000 ký tự, cho phép `null`.
- `price_cents`: số nguyên không âm; tên trường biểu thị đơn vị cent, không tự quy đổi tiền tệ.
- `qty_in_stock`: số nguyên không âm, mặc định `0` khi tạo mới.
- Phân trang mặc định `page=1`, `size=20`; `page >= 1`, `1 <= size <= 100`.
- Reserve yêu cầu `qty` nguyên dương. Điều kiện đủ hàng và giảm kho nằm trong cùng lệnh UPDATE.
- List/get loại sản phẩm đã archive; PATCH và reserve cũng không xử lý sản phẩm đã archive.

### Order

| Method | Endpoint | Chức năng | Thành công |
|---|---|---|---|
| POST | `/api/v1/orders` | Tạo đơn với nhiều dòng hàng | 201 |
| GET | `/api/v1/orders` | Danh sách đơn cùng dòng hàng và sản phẩm | 200 |
| GET | `/api/v1/orders/{id}` | Chi tiết một đơn | 200 |

Body tạo đơn có từ 1–100 dòng hàng, không lặp Product. API tự lấy giá Product để lưu vào `unit_price_cents`, không nhận đơn giá từ client.

Trong bài này, tạo Order đồng thời giảm kho. Toàn bộ đơn chỉ được commit khi xử lý thành công tất cả mặt hàng; lỗi giữa chừng sẽ rollback cả đơn và phần giảm kho. Không gọi `/reserve` trước cho cùng số lượng hàng rồi tiếp tục tạo Order, vì chưa có cơ chế liên kết reservation với đơn.

Đổi giá Product không làm đổi đơn giá đã lưu trong OrderItem. Sản phẩm đã archive vẫn có thể xuất hiện trong đơn hàng lịch sử.

GET Order dùng `selectinload(Order.items).selectinload(OrderItem.product)` để nạp trước dữ liệu, tránh truy vấn riêng cho từng đơn hoặc từng dòng hàng khi serialize. Danh sách Order hiện chưa phân trang.

## Ví dụ gọi API trên Swagger

### 1. Tạo hai sản phẩm

Gửi riêng từng body tới `POST /api/v1/products`:

```json
{
  "sku": "MOUSE-001",
  "name": "Chuột không dây",
  "description": "Chuột kết nối USB receiver",
  "price_cents": 25000,
  "qty_in_stock": 20
}
```

```json
{
  "sku": "HEADSET-001",
  "name": "Tai nghe có dây",
  "description": "Tai nghe có micro",
  "price_cents": 45000,
  "qty_in_stock": 15
}
```

Ghi lại ID thực tế từ hai response `201`. Gửi lại SKU đã có sẽ trả `409`.

### 2. Tạo đơn hàng

Gửi tới `POST /api/v1/orders`; thay `1`, `2` bằng ID thực tế:

```json
{
  "items": [
    {"product_id": 1, "qty": 2},
    {"product_id": 2, "qty": 1}
  ]
}
```

Nếu đủ hàng, API trả `201`, có hai dòng `items`. Với hai sản phẩm mới ở trên, tồn kho lần lượt còn `18` và `14`. Dùng `GET /api/v1/orders/{id}` để đọc lại đơn vừa tạo.

### 3. Thử riêng reserve và PATCH

Body cho `POST /api/v1/products/{id}/reserve`:

```json
{"qty": 1}
```

Body cho `PATCH /api/v1/products/{id}`:

```json
{"name": "Tên sản phẩm mới"}
```

PATCH trên chỉ đổi tên; giá và tồn kho được giữ nguyên. DELETE trả `204` không có body; GET sản phẩm đó sau khi archive trả `404`.

## Xử lý lỗi

Lỗi trả HTTP status phù hợp và JSON thống nhất, ví dụ:

```json
{
  "error": "out_of_stock",
  "detail": "Only 0 item(s) available."
}
```

| HTTP status | Trường hợp |
|---|---|
| 404 | Không tìm thấy Order hoặc Product phù hợp; Product đã archive không được dùng để tạo đơn mới |
| 409 | Trùng SKU hoặc tồn kho không đủ |
| 422 | Dữ liệu không hợp lệ: giá âm, số lượng sai, dòng hàng trùng, query phân trang sai |
| 500 | Lỗi ngoài dự kiến; chi tiết được ghi trong log server |

Lỗi validation cũng dùng `error`, `detail`; `detail` chứa chuỗi mô tả lỗi theo trường. Readiness có response riêng theo trạng thái probe như phần dưới.

## Liveness và readiness

| Endpoint | Kiểm tra | Khi DB không truy cập được |
|---|---|---|
| `/healthz` | Ứng dụng còn xử lý request; không gọi DB | Vẫn 200 nếu API còn hoạt động |
| `/ready` | Truy vấn `SELECT 1` tới DB | 503 |

Readiness chỉ kiểm tra khả năng truy cập DB, không kiểm tra toàn bộ bảng hoặc tình trạng migration. Compose hiện dùng `pg_isready` để chờ PostgreSQL; chưa cấu hình healthcheck cho container API.

Thử tại `B7/Lab1` khi API Docker đang chạy:

```powershell
curl.exe -i http://localhost:5000/healthz
curl.exe -i http://localhost:5000/ready

# Dừng riêng DB: healthz phải vẫn 200, ready chuyển sang 503
docker compose stop db
curl.exe -i http://localhost:5000/healthz
curl.exe -i http://localhost:5000/ready

# Khôi phục DB, đợi sẵn sàng rồi kiểm tra ready trở lại 200
docker compose start db
curl.exe -i http://localhost:5000/ready
```

Khi DB hoạt động, `/ready` trả:

```json
{"status": "ok", "checks": {"db": "ok"}}
```

Khi kết nối DB lỗi, `/ready` trả `503`:

```json
{"status": "degraded", "checks": {"db": "error"}}
```

## Chạy kiểm thử

Tại `B7/Lab1`, kích hoạt virtual environment rồi chạy:

```powershell
python -m pip install -e ".[test]"
python -m pytest -v
```

Không cần chạy server hoặc Docker. Mỗi test tạo app và SQLite trong bộ nhớ riêng, không dùng database thực hành. Fixture tạo bảng từ model để kiểm tra API; bộ test này không thay thế kiểm tra migration trên PostgreSQL.

| Test | Nội dung |
|---|---|
| `test_create_order` | POST tạo đơn có hai Product; kiểm tra dữ liệu, đơn giá và tồn kho |
| `test_create_order_rolls_back` | Mặt hàng sau thiếu kho thì không lưu đơn và không mất kho mặt hàng trước |
| `test_list_orders_uses_eager_loading` | GET trả đủ dữ liệu lồng nhau cho 5 đơn với 5 Product khác nhau, dùng 3 SELECT |

Kết quả mong đợi: `3 passed`. Test đếm truy vấn chỉ tính trong request GET, sau khi đóng session chuẩn bị dữ liệu; không tính truy vấn seed. Con số 3 áp dụng cho bộ dữ liệu nhỏ của test, vì `selectinload` có thể chia batch khi dữ liệu lớn.
