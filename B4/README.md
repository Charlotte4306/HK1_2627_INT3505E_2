# Buổi 4 · Phần 4 — Flask + apispec

Tasks API với 5 endpoint. apispec sinh OpenAPI 3.0.3 từ marshmallow Schema và YAML docstring.

- `app.py`: Flask app + apispec
- `openapi.yaml`: spec xuất từ app (giống nội dung `GET /openapi.yaml`)

## Endpoint

| Method | URL | Mô tả |
|---|---|---|
| GET | `/api/v1/tasks?status=` | Lấy danh sách task |
| POST | `/api/v1/tasks` | Tạo task mới |
| GET | `/api/v1/tasks/<task_id>` | Lấy task theo id |
| PATCH | `/api/v1/tasks/<task_id>` | Cập nhật một phần task |
| DELETE | `/api/v1/tasks/<task_id>` | Xoá task |
| GET | `/openapi.json` | Spec dạng JSON |
| GET | `/openapi.yaml` | Spec dạng YAML |
| GET | `/docs` | Swagger UI |

## Các bước sinh spec

1. **Schema → JSON Schema**: `MarshmallowPlugin` chuyển `TaskSchema`, `UpdateTaskSchema`, `TaskListSchema`, `ErrorSchema` thành `components.schemas`.
2. **Docstring → paths**: `FlaskPlugin` đọc phần YAML sau dấu `---` trong docstring của từng route, rồi đăng ký bằng `spec.path(view=...)`.
3. **`/openapi.json`** trả về `spec.to_dict()`.
4. **`/docs`** hiển thị Swagger UI từ CDN, đọc spec từ `/openapi.json`.
