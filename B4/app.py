from flask import Flask, jsonify, request, url_for
from marshmallow import Schema, ValidationError, fields, validate

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.yaml_utils import dict_to_yaml
from apispec_webframeworks.flask import FlaskPlugin

app = Flask(__name__)

TASKS = []
next_task_id = 1

STATUSES = ["open", "in_progress", "done"]
PRIORITIES = ["low", "normal", "high"]

#Schema của task, MarshmallowPlugin sẽ dịch sang JSON Schema trong spec
class TaskSchema(Schema):
    id = fields.Int(dump_only=True, metadata={"example": 1})
    title = fields.Str(required=True, validate=validate.Length(min=1),
                       metadata={"example": "Viết spec Tasks API"})
    status = fields.Str(load_default="open", validate=validate.OneOf(STATUSES),
                        metadata={"example": "open"})
    priority = fields.Str(load_default="normal", validate=validate.OneOf(PRIORITIES),
                          metadata={"example": "high"})
    due_date = fields.Date(load_default=None, allow_none=True, metadata={"example": "2026-10-20"})
    assignee_id = fields.Int(load_default=None, allow_none=True, metadata={"example": 101})

#Schema cho PATCH, các field đều không bắt buộc
class UpdateTaskSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1))
    status = fields.Str(validate=validate.OneOf(STATUSES))
    priority = fields.Str(validate=validate.OneOf(PRIORITIES))
    due_date = fields.Date(allow_none=True)
    assignee_id = fields.Int(allow_none=True)

class TaskListSchema(Schema):
    data = fields.List(fields.Nested(TaskSchema))
    total = fields.Int(metadata={"example": 1})

class ErrorSchema(Schema):
    error = fields.Str(metadata={"example": "Task not found"})
    details = fields.Dict()

task_schema = TaskSchema()
update_task_schema = UpdateTaskSchema()

#Tạo spec, FlaskPlugin đọc route + docstring, MarshmallowPlugin đọc schema
spec = APISpec(
    title="Tasks API",
    version="1.0.0",
    openapi_version="3.0.3",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)

#Đăng ký schema vào components để các route dùng lại qua $ref
spec.components.schema("Task", schema=TaskSchema)
spec.components.schema("UpdateTask", schema=UpdateTaskSchema)
spec.components.schema("TaskList", schema=TaskListSchema)
spec.components.schema("Error", schema=ErrorSchema)

#Tìm task theo id
def find_task(task_id):
    for task in TASKS:
        if task["id"] == task_id:
            return task
    return None

#Lấy danh sách task, có thể lọc theo status
@app.get("/api/v1/tasks")
def list_tasks():
    status = request.args.get("status")

    tasks = TASKS
    if status:
        tasks = [task for task in tasks if task["status"] == status]

    return jsonify({
        "data": task_schema.dump(tasks, many=True),
        "total": len(tasks)
    }), 200

#Tạo task mới
@app.post("/api/v1/tasks")
def create_task():
    global next_task_id

    if not request.is_json:
        return jsonify(error="expected JSON"), 415

    try:
        data = task_schema.load(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(error="invalid data", details=e.messages), 422

    task = {"id": next_task_id, **data}
    TASKS.append(task)
    next_task_id += 1

    location = url_for("get_task", task_id=task["id"], _external=True)
    return jsonify(task_schema.dump(task)), 201, {"Location": location}

#Lấy task theo id
@app.get("/api/v1/tasks/<int:task_id>")
def get_task(task_id):
    task = find_task(task_id)
    if task is None:
        return jsonify(error="Task not found"), 404

    return jsonify(task_schema.dump(task)), 200

#Cập nhật một phần task
@app.patch("/api/v1/tasks/<int:task_id>")
def patch_task(task_id):
    task = find_task(task_id)
    if task is None:
        return jsonify(error="Task not found"), 404

    if not request.is_json:
        return jsonify(error="expected JSON"), 415

    try:
        data = update_task_schema.load(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(error="invalid data", details=e.messages), 422

    task.update(data)
    return jsonify(task_schema.dump(task)), 200

#Xoá task
@app.delete("/api/v1/tasks/<int:task_id>")
def delete_task(task_id):
    task = find_task(task_id)
    if task is None:
        return jsonify(error="Task not found"), 404

    TASKS.remove(task)
    return "", 204

with app.test_request_context():
    spec.path(view=list_tasks)
    spec.path(view=create_task)
    spec.path(view=get_task)
    spec.path(view=patch_task)
    spec.path(view=delete_task)

@app.get("/openapi.json")
def openapi_json():
    return jsonify(spec.to_dict()), 200

@app.get("/openapi.yaml")
def openapi_yaml():
    spec_dict = spec.to_dict()
    ordered = {
        "openapi": spec_dict.pop("openapi"),
        "info": spec_dict.pop("info"),
        **spec_dict
    }

    yaml_text = dict_to_yaml(ordered, {"allow_unicode": True, "sort_keys": False})
    return yaml_text, 200, {"Content-Type": "application/yaml; charset=utf-8"}

SWAGGER_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Tasks API - Swagger UI</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({ url: "/openapi.json", dom_id: "#swagger-ui" });
  </script>
</body>
</html>"""


@app.get("/docs")
def docs():
    return SWAGGER_HTML

if __name__ == "__main__":
    app.run(port=5000, debug=True)
