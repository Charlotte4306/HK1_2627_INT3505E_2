# [HK1_2627_INT3505E_2_Group9]

# Đánh giá Spotify Web API

- Họ tên: Lê Thị Nhung
- MSSV: 24020261
- Nhóm: 9
- Tiêu chí được phân công: Tiêu chí 7 và tiêu chí 8

## Tiêu chí 7: Filter/Sort đa dạng

**Yêu cầu:** Hỗ trợ lọc theo trường chính, sắp xếp đa trường và chọn trường trả về (sparse fieldsets).

| Nội dung | Đánh giá Spotify Web API |
|---|---|
| Lọc dữ liệu | Search hỗ trợ lọc theo các trường như `artist`, `album`, `track`, `year`, `genre`; bộ lọc áp dụng tùy loại kết quả. |
| Sắp xếp đa trường | Search và Get Playlist Items không công bố tham số sort đa trường. |
| Chọn trường trả về | Get Playlist Items hỗ trợ `fields`, ví dụ `fields=total,limit,items(added_at)`. |

Ví dụ lọc bài hát theo nghệ sĩ và khoảng năm:

```http
GET /v1/search?q=artist%3AColdplay%20year%3A2020-2024&type=track
Authorization: Bearer <access_token>
```

**Kết quả: Không đạt đầy đủ.** Có lọc dữ liệu và chọn trường trả về, nhưng chưa đáp ứng yêu cầu sort đa trường trong các endpoint khảo sát.

**Vấn đề và đề xuất:** Thiếu sort phía server khiến ứng dụng phải tự xử lý sắp xếp; nếu chỉ xử lý một trang thì không sắp xếp được toàn bộ kết quả. Đề xuất bổ sung tham số sort tại collection phù hợp, ví dụ thiết kế `sort=name,-duration_ms`, đồng thời công bố các trường được phép sắp xếp.


## Tiêu chí 8: Authentication & security

**Yêu cầu:** Token nằm trong header, không truyền access token qua URL và có cơ chế rate limit rõ ràng.

| Nội dung | Đánh giá Spotify Web API |
|---|---|
| Xác thực và phân quyền | Sử dụng OAuth 2.0; scope xác định quyền truy cập. PKCE được khuyến nghị cho mobile và SPA không bảo vệ được client secret. |
| Truyền token | Tài liệu hướng dẫn gửi `Authorization: Bearer <access_token>` trong header, không đặt access token vào URL của request tài nguyên. |
| Rate limit | Tính theo cửa sổ trượt 30 giây; khi vượt giới hạn có thể trả `429 Too Many Requests`, thường kèm `Retry-After` tính bằng giây. |

Ví dụ truyền token:

```http
GET /v1/search?q=Coldplay&type=track
Authorization: Bearer <access_token>
```

**Kết quả: Đạt theo phạm vi checklist.** Cơ chế truyền token và xử lý rate limit được tài liệu hóa. Đây không phải kết luận kiểm toán bảo mật toàn diện.

**Vấn đề và đề xuất:** Spotify không công bố một ngưỡng request cố định áp dụng chung cho mọi ứng dụng; hạn mức phụ thuộc chế độ app và có thể có ngoại lệ theo endpoint. Đề xuất cung cấp thông tin hạn mức tương ứng với từng app rõ hơn qua Dashboard hoặc response. Ứng dụng cần tuân thủ `Retry-After`, giới hạn số lần retry và không đưa token hoặc client secret lên repository.
