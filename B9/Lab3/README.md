# B9 Lab 3 — Sunset middleware

`@deprecate_at` ghi log `deprecated_call` mỗi khi endpoint v1 được gọi. Trước mốc sunset, v1 vẫn xử lý yêu cầu. Từ đúng mốc đó, v1 trả `410 Gone` với `sunset` và `use_instead` trong JSON. Cả hai trạng thái có header `Sunset`, `Deprecation: true` và `Link` trỏ tới endpoint v2.

## Chạy thử trên PowerShell

Mở terminal ở `B9/Lab3` với môi trường Python đã cài Flask. Đặt mốc ở tương lai để thử HTTP 200:

```powershell
$env:LAB3_V1_SUNSET = (Get-Date).ToUniversalTime().AddDays(1).ToString("o")
python -m flask --app app run --port 5003
```

Ở terminal khác, xem status, header và JSON:

```powershell
curl.exe -i http://127.0.0.1:5003/api/v1/users/1
curl.exe -i http://127.0.0.1:5003/api/v2/users
```

Để thử HTTP 410, dừng server bằng `Ctrl+C` rồi chạy lại với mốc đã qua:

```powershell
$env:LAB3_V1_SUNSET = (Get-Date).ToUniversalTime().AddDays(-1).ToString("o")
python -m flask --app app run --port 5003
```

Gọi lại v1 và xem dòng `deprecated_call` trong terminal server. Mốc mặc định theo slide là `2026-12-31T23:59:59+00:00`. Định dạng `Deprecation: true` được giữ theo yêu cầu bài lab.
