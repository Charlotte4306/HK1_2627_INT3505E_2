# Lab 4 — Phân tích load test Books API

## Môi trường và cách đo

- Ngày chạy: 15/11/2026. Windows 11 x64, CPU AMD64 Family 25 Model 68, 16 logical CPU; Python 3.14.2, Locust 2.47.0.
- Load generator và API cùng máy. Dùng application factory `create_app()` của starter, Flask development server threaded, SQLite; không sửa `app.py` hoặc `models.py`.
- API đo tại `http://127.0.0.1:5001` để tách khỏi server làm bài ở cổng 5000. Mỗi kịch bản dùng file SQLite tạm mới trong workspace, tạo 50 sách có ID 1–50, author `lab4-seed`, title `Seed book n`, year `(2017, 2021, 2024)[n % 3]`. DB mặc định `instance/books.db` không bị thay đổi bởi load test.
- Chạy A → B → C tuần tự. Trọng số task list/read/create/search là 3/2/1/2; user nghỉ ngẫu nhiên 1–3 giây. POST tạo thêm sách có năm thuộc 2017/2021/2024. Search được nhóm chung tên để không chia nhỏ thống kê theo query.
- Mỗi cấu hình chạy một lần, có cả giai đoạn ramp-up, không reset stats sau ramp-up. Số user là user mô phỏng tối đa, không phải tất cả cùng giữ kết nối DB. Thời lượng lệnh là 30/60/30 giây; khoảng đo request trong HTML là 28/59/29 giây vì Locust bắt đầu tính thống kê sau khởi động. RPS lấy từ `total_rps`, không lấy RPS tức thời.
- Mọi số liệu dưới đây được trích trực tiếp từ dữ liệu cuối `window.templateArgs` trong 3 HTML, không phải số giả định. Percentile của Locust là giá trị xấp xỉ.

## Kết quả tổng hợp

| Kịch bản | Users | Spawn/s | Thời lượng cấu hình | Requests | p95 (ms) | Failures | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | 136 | 12 | 0 | 0.000% | 4.72 |
| B | 50 | 5 | 60s | 1404 | 14 | 3 | 0.214% | 23.76 |
| C | 200 | 50 | 30s | 2798 | 98 | 6 | 0.214% | 95.86 |

Failure rate = số request Locust đánh dấu lỗi / tổng request. Tất cả lỗi ở đây là injection phía client; log HTTP của server ghi 0 response 5xx trong cả A/B/C.

### Chi tiết theo endpoint

| Endpoint | A p95 | B p95 | C p95 | A lỗi / request | B lỗi / request | C lỗi / request |
|---|---:|---:|---:|---:|---:|---:|
| GET /books | 9 ms | 10 ms | 100 ms | 0/53 | 0/535 | 0/1056 |
| GET /books/{id} | 7 ms | 9 ms | 80 ms | 0/40 | 0/363 | 0/695 |
| GET /books?year={year} | 7 ms | 9 ms | 100 ms | 0/29 | 3/352 | 6/707 |
| POST /books | 16 ms | 24 ms | 110 ms | 0/14 | 0/154 | 0/340 |

## 1. Kịch bản nào có p95 cao nhất? Vì sao?

C cao nhất: 98 ms, so với A 12 ms và B 14 ms. Dãy (users, p95) là (10, 12), (50, 14), (200, 98). RPS tăng từ 4.72 lên 23.76 rồi 95.86. Khi tăng từ 50 lên 200 user, p95 tăng mạnh hơn đoạn 10 lên 50.

POST là endpoint chậm nhất ở C với p95 110 ms; các thao tác đọc có p95 80–100 ms. Việc phải ghi/commit SQLite, cạnh tranh tài nguyên giữa các request và CPU dùng chung với load generator có thể làm tăng độ trễ. Đây là giả thuyết phù hợp số liệu, chưa phải chứng minh nguyên nhân: chưa đo CPU, thời gian chờ DB/lock hoặc pool. Một lần chạy ngắn cũng chưa xác định được điểm bão hòa hoặc quy luật tăng phi tuyến.

## 2. Endpoint nào tăng failure rate?

Chỉ `GET /books?year={year}` có lỗi: A 0/29 = 0%, B 3/352 ≈ 0.852%, C 6/707 ≈ 0.849%. Số lỗi tăng theo số request; tỷ lệ từ B sang C gần như không đổi, nên không có bằng chứng backend tăng failure rate theo user trong phép đo này.

Trong `search_by_year`, response thực phải là HTTP 200 trước; sau đó `random.random() < 0.01` đánh dấu `response.failure("SIMULATED_500: client-side injection (actual HTTP 200)")`. Đây là mô phỏng lỗi 500 trong thống kê client, không thay status HTTP và không tạo lỗi server. Xác suất 1% áp dụng cho request search HTTP 200, không phải toàn bộ request. Vì search có trọng số 2/8, tỷ lệ lỗi tổng kỳ vọng khoảng 0.25%, và số quan sát có thể khác do lấy mẫu ngẫu nhiên. A chỉ có 29 search nên 0 lỗi vẫn hợp lý.

Các endpoint khác không có lỗi trong lần đo này. Starter coi GET theo ID trả 200 hoặc 404 là thành công; vì vậy bảng failure không tự chứng minh mọi ID đều tồn tại. 50 ID đã seed giúp workload đọc theo ID có dữ liệu thật.

## 3. SLO p95 < 300 ms và baseline CI

Cả A, B, C đạt điều kiện độ trễ giả định: p95 tổng lần lượt 12, 14, 98 ms; p95 từng endpoint cũng đều < 300 ms. POST ở C có max 387 ms nhưng điều đó không mâu thuẫn p95 < 300 ms: p95 không phải maximum.

Đề xuất A (10 user, spawn 2/s, 30s) làm baseline kiểm tra hiệu năng nhanh cho CI. Gate ban đầu: p95 tổng và từng endpoint < 300 ms, không có lỗi HTTP/transport thật hoặc exception task. Phải phân loại lỗi có nhãn SIMULATED_500 riêng; không dùng exit code Locust đơn lẻ làm gate vì injection có thể khiến process trả 1. B có thể chạy định kỳ để theo dõi thay đổi dưới tải cao hơn.

Chưa thể dùng các số này khẳng định SLO production: Flask development server + SQLite, cùng máy với Locust, DB nhỏ, mỗi cấu hình chỉ đo một lần, think-time 1–3 giây, thời gian ngắn và có ramp-up. Cần lặp lại nhiều lần trên môi trường ổn định, load generator riêng và workload/dataset thực tế trước khi đặt ngưỡng CI chặt hơn hoặc kết luận năng lực hệ thống.

## 4. Bonus: connection pool giới hạn 5 với 200 user

Nếu giới hạn thực sự 5 connection (`pool_size=5`, `max_overflow=0`), các request giữ connection vượt 5 phải chờ connection được trả. Chờ pool có thể tăng response time/p95; nếu chờ vượt `pool_timeout` có thể phát sinh TimeoutError và HTTP 500 nếu không được xử lý. Không có nghĩa 195 user chắc chắn lỗi: user còn think-time, HTTP/CPU và thời gian giữ connection có thể rất ngắn. Chỉ đặt pool_size=5 mà vẫn cho overflow cũng chưa phải giới hạn cứng 5.

Cách kiểm chứng: tạo hai cấu hình application factory riêng trong môi trường thử, giữ nguyên DB ban đầu và kịch bản C; một cấu hình baseline, một cấu hình `SQLALCHEMY_ENGINE_OPTIONS` với `pool_size=5`, `max_overflow=0`, `pool_timeout` đã ghi rõ. So sánh p95/RPS và lỗi HTTP thật trong Locust, đồng thời kiểm tra server log có QueuePool timeout và đo thời gian chờ pool. Giữ injection giống nhau hoặc tắt ở cả hai lượt để tránh nhầm lẫn. Chưa chạy thí nghiệm giới hạn pool trong bài này; không suy diễn rằng C hiện tại đã bị nghẽn pool.



Nguồn tham khảo: [Locust catch_response và response.failure](https://docs.locust.io/en/stable/writing-a-locustfile.html#validating-responses), [tham số chạy và xuất HTML](https://docs.locust.io/en/stable/config-options.html).
