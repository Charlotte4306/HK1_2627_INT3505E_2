"""Xuất hợp đồng được sinh từ code; không viết/sửa file JSON này bằng tay."""
import json
from pathlib import Path

if __package__:
    from .app import api
else:
    from app import api


if __name__ == "__main__":
    spec = api.spec.to_dict()
    target = Path(__file__).with_name("openapi.generated.json")
    target.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)
