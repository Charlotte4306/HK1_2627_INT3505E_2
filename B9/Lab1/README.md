# B9 Lab 1 — Phiên bản API theo đường dẫn

Hai Flask Blueprint dùng chung dữ liệu người dùng. V1 trả `full_name`, còn v2 trả `first_name` và `last_name`. V2 hỗ trợ tạo người dùng qua POST. Dữ liệu mới được lưu trong bộ nhớ đến khi server khởi động lại.

## Chạy thử trên PowerShell

Từ thư mục `B9/Lab1`, dùng môi trường Python đã cài Flask (`python -m pip install flask` nếu cần):

```powershell
python -m flask --app app run --port 5001
```

Mở terminal khác để gọi API:

```powershell
curl.exe -i http://127.0.0.1:5001/api/v1/users/1
curl.exe -i http://127.0.0.1:5001/api/v2/users/1
$body = @{first_name = "An"; last_name = "Tran"; email = "an@example.com"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5001/api/v2/users -ContentType application/json -Body $body
```

Lệnh GET v1 hiển thị header `Sunset` với mốc minh họa 01/01/2027 lúc 00:00 UTC. Để đổi ngày, đặt `$env:LAB1_V1_SUNSET_DATE = "2027-06-01"` trước khi chạy server.

Xem đặc tả API trong [openapi.yaml](openapi.yaml).
