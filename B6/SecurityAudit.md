# Security Audit — Social Network API

## 1. Tổng quan

Hệ thống Social Network API sử dụng JWT (JSON Web Token) để xác thực người dùng và kiểm tra scope để phân quyền truy cập tài nguyên.

Các endpoint được kiểm tra:

- `POST /auth/login`
- `POST /auth/refresh`
- `GET /posts/{id}`

Mục tiêu là nhận diện các lỗ hổng tiềm ẩn và đề xuất giải pháp giảm thiểu rủi ro bảo mật.

## 2. Danh sách lỗ hổng

### 2.1. Brute-force Attack vào Login

**Mức độ:** High

**Endpoint:** `POST /auth/login`

**Mô tả:** Kẻ tấn công có thể gửi liên tục các yêu cầu đăng nhập với nhiều mật khẩu khác nhau để dò tìm thông tin đăng nhập.

**Giải pháp:**
- Áp dụng rate limiting.
- Giới hạn số lần đăng nhập thất bại.
- Ghi log và phát hiện hành vi bất thường.
- Cân nhắc MFA khi phù hợp.

### 2.2. Lưu mật khẩu không an toàn

**Mức độ:** Critical

**Endpoint:** `POST /auth/login`

**Mô tả:** Nếu mật khẩu được lưu dưới dạng plaintext hoặc sử dụng thuật toán hash không phù hợp, việc rò rỉ cơ sở dữ liệu có thể làm lộ thông tin đăng nhập.

**Giải pháp:**
- Sử dụng Argon2id hoặc bcrypt.
- Hash mật khẩu với salt phù hợp.
- Không ghi mật khẩu vào log.
- Không trả thông tin mật khẩu trong response.

### 2.3. JWT Token bị đánh cắp

**Mức độ:** High

**Endpoint:** Các endpoint có xác thực.

**Mô tả:** Nếu token bị lộ qua XSS, log hoặc lưu trữ không an toàn, người khác có thể sử dụng token để truy cập API.

**Giải pháp:**
- Chỉ sử dụng HTTPS.
- Access token có thời hạn ngắn, ví dụ 15 phút.
- Không ghi token vào log.
- Cân nhắc cookie HttpOnly, Secure, SameSite cho ứng dụng web và bổ sung biện pháp chống CSRF.
- Thiết kế cơ chế thu hồi token.

### 2.4. Refresh Token Replay

**Mức độ:** High

**Endpoint:** `POST /auth/refresh`

**Mô tả:** Refresh token bị đánh cắp có thể được sử dụng nhiều lần để lấy access token mới nếu server không có cơ chế kiểm soát và thu hồi.

**Giải pháp:**
- Triển khai refresh token rotation.
- Phát hiện hành vi sử dụng lại refresh token.
- Thu hồi phiên khi phát hiện token bị tái sử dụng trái phép.
- Lưu trạng thái token hoặc phiên để hỗ trợ thu hồi.

### 2.5. Broken Object Level Authorization (BOLA)

**Mức độ:** Critical

**Endpoint:** `GET /posts/{id}`

**Mô tả:** Người dùng có thể thay đổi ID của bài viết trong URL để cố truy cập bài viết riêng tư của người khác. Nếu backend chỉ kiểm tra JWT mà không kiểm tra quyền trên từng bài viết, dữ liệu riêng tư có thể bị lộ.

**Giải pháp:**
- Kiểm tra quyền sở hữu tài nguyên.
- Kiểm tra trạng thái public/private.
- Không chỉ dựa vào việc token hợp lệ.
- Với tài nguyên riêng tư không được phép tiết lộ sự tồn tại, cân nhắc trả 404.

### 2.6. Thiếu kiểm tra scope

**Mức độ:** High

**Endpoint:** `GET /posts/{id}`

**Mô tả:** Server chỉ xác minh chữ ký JWT mà không kiểm tra scope có thể cho phép token không đủ quyền đọc tài nguyên.

**Giải pháp:**
- Yêu cầu scope `posts:read`.
- Trả HTTP 403 khi thiếu quyền.
- Áp dụng nguyên tắc Least Privilege.
- Kiểm tra quyền tại backend.

### 2.7. JWT Validation không đầy đủ

**Mức độ:** Critical

**Endpoint:** Các endpoint sử dụng JWT.

**Mô tả:** Nếu server không kiểm tra thuật toán ký, chữ ký và các claims quan trọng, hệ thống có thể chấp nhận token không hợp lệ hoặc token được cấp cho dịch vụ khác.

**Giải pháp:**
- Chỉ chấp nhận thuật toán ký trong allowlist.
- Xác minh chữ ký bằng khóa tin cậy.
- Kiểm tra `exp`, `nbf`, `iss`, `aud` theo cấu hình.
- Phân biệt access token và refresh token.
- Quản lý và thay đổi khóa ký an toàn.

## 3. Kết luận

Quá trình đánh giá đã nhận diện 7 nhóm lỗ hổng tiềm ẩn trong hệ thống Social Network API.

Các rủi ro cần ưu tiên xử lý là:

1. BOLA — truy cập trái phép bài viết riêng tư.
2. JWT validation không đầy đủ.
3. Lưu trữ mật khẩu không an toàn.
4. Refresh token bị sử dụng lại.
5. Thiếu giới hạn yêu cầu và kiểm soát scope.

Hệ thống cần kết hợp Authentication, Authorization, scope và kiểm tra quyền sở hữu tài nguyên thay vì chỉ dựa vào việc JWT hợp lệ.

