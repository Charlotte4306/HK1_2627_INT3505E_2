# Bài 2 — Flask pagination (offset + cursor, filter, sort multi-key)

Mở rộng `list_books` của Lab 1: một endpoint `GET /api/v1/books` hỗ trợ cả phân trang **offset** và **cursor** (chọn qua `?strategy=`), lọc theo `?genre` và sort theo nhiều cột.

## Luồng hoạt động

- `list_books`: đọc `strategy` (mặc định `offset`), `limit`, `sort`, `genre`. Kiểm tra tham số (sai thì trả `400`), dựng một query chung đã sort và lọc, rồi chuyển sang `paginate_offset` hoặc `paginate_cursor`.
- `parse_sort`: tách `?sort=-price,title` thành danh sách `(cột, chiều)`. Chỉ nhận cột trong whitelist `id`, `title`, `price`, `stock`; dấu `-` là giảm dần. Cột lạ hoặc bị lặp thì trả `400 bad_sort`. Luôn thêm `id` vào cuối để sách bằng nhau ở mọi cột vẫn có thứ tự cố định.
- `apply_genre`: model không có cột genre nên genre chính là `Category.slug`. `?genre=tech,novel` join với bảng `categories` và lọc bằng `IN`.
- `paginate_offset`: bỏ qua `offset` dòng, lấy `limit` dòng. Đếm `total` sau khi lọc để tính `has_next`. `offset` âm thì trả `400`.
- `paginate_cursor`: lấy dư 1 dòng (`limit + 1`) để biết còn trang sau không. Cursor là base64 của `{"s": sort, "v": [giá trị các cột sort của sách cuối trang]}`. Trang sau lọc bằng điều kiện keyset `keyset_condition`:
  `(a > va) OR (a = va AND b < vb) OR (a = va AND b = vb AND id > vi)`
  Mỗi cột so sánh theo chiều riêng, nên đúng cả khi các cột sort ngược chiều nhau (ví dụ `price,-stock`). Cursor hỏng thì trả `invalid_cursor`, dùng cursor với `sort` khác thì trả `sort_changed`.
- `app.py`: chuyển sang `create_app(config)` để test truyền được DB in-memory. Seed 8 sách, trong đó có các cặp trùng giá (520000, 450000, 60000) để kiểm tra sort nhiều cột.

---

## Tham số của `GET /api/v1/books`

| Tham số | Giá trị | Mặc định | Ghi chú |
|---|---|---|---|
| `strategy` | `offset`, `cursor` | `offset` | Giá trị khác → `400 bad_strategy` |
| `limit` | 1 – 100 | 20 | Lớn hơn 100 bị cắt về 100, nhỏ hơn 1 → `400` |
| `offset` | ≥ 0 | 0 | Chỉ dùng với `strategy=offset` |
| `cursor` | `next_cursor` của trang trước | — | Chỉ dùng với `strategy=cursor`, phải giữ nguyên `sort` |
| `sort` | `id`, `title`, `price`, `stock`; `-` là giảm dần; nối bằng `,` | `id` | Ví dụ `-price,title` |
| `genre` | slug category, nối bằng `,` | — | Ví dụ `novel`, `tech,novel` |

Phần `pagination` trong response:

```json
// strategy=offset
{ "strategy": "offset", "offset": 0, "limit": 3, "total": 8, "has_next": true }

// strategy=cursor
{ "strategy": "cursor", "limit": 3, "next_cursor": "eyJzIjogIi1wcmljZS...", "has_more": true }
```


---

## Chạy và test

```bash
pip install flask flask-sqlalchemy jsonschema pytest
python app.py
```


Chạy test (dùng SQLite in-memory, không cần bật server):

```bash
python -m pytest -q
```

19 test trong `tests/test_list_books.py`, chia theo nhóm:

- **offset**: mặc định là offset, đúng trang và `has_next`, offset âm.
- **cursor**: đi hết các trang không lặp/sót, thứ tự khớp với offset, đổi sort (`sort_changed`), cursor hỏng (`invalid_cursor`).
- **genre**: một genre, nhiều genre, genre không tồn tại, genre kết hợp cursor.
- **sort**: nhiều cột, ngược chiều, cột lạ, cột lặp.
- **validate**: strategy sai, `limit` quá nhỏ hoặc quá lớn.0

**Postman:** Import `postman/books_pagination.postman_collection.json` (12 request, biến `baseUrl` và `next_cursor`). Request "Cursor - trang đầu" tự lưu `next_cursor` cho các request sau, nên chạy nó trước hoặc dùng **Run collection**.

