# B9 Lab 4 — Blue-Green routing

`POST /orders` chọn v2 theo thứ tự: header `X-Cohort` là `beta` hoặc `internal`, tài khoản nằm trong allow-list (`acct_42`, `acct_99`), rồi đến bucket `MD5(account_id) % 100` nhỏ hơn `V2_PERCENT`. Cùng một tài khoản có bucket cố định. V1 trả `200`, v2 trả `201`. Header `X-Order-Handler` cho biết handler đã xử lý yêu cầu. Hai handler mô phỏng việc tạo đơn hàng trong bài lab.

Mở PowerShell tại `B9/Lab4` với môi trường Python đã cài Flask:

```powershell
$env:V2_PERCENT = '5'
python -m flask --app app run --port 5004
```

Ở terminal khác, chạy:

```powershell
$url = 'http://127.0.0.1:5004/orders'
$ordinary = @{account_id = 'acct_1'} | ConvertTo-Json -Compress
$allowed = @{account_id = 'acct_42'} | ConvertTo-Json -Compress
$inBucket = @{account_id = 'acct_72'} | ConvertTo-Json -Compress

Invoke-WebRequest -UseBasicParsing -Method Post -Uri $url -ContentType 'application/json' -Body $ordinary -Headers @{'X-Cohort' = 'beta'}
Invoke-WebRequest -UseBasicParsing -Method Post -Uri $url -ContentType 'application/json' -Body $allowed
Invoke-WebRequest -UseBasicParsing -Method Post -Uri $url -ContentType 'application/json' -Body $ordinary
Invoke-WebRequest -UseBasicParsing -Method Post -Uri $url -ContentType 'application/json' -Body $inBucket
```

Kết quả theo thứ tự là **v2, v2, v1, v2**. Hai tài khoản thường có bucket 53 (`acct_1`) và 3 (`acct_72`).

Để thử rollout 100%, dừng Flask, đổi `$env:V2_PERCENT = '100'` rồi chạy lại. Gửi lại `acct_1` không kèm header sẽ nhận `201` và `X-Order-Handler: v2`. Nếu cần quay lui, đặt lại `5` và khởi động lại Flask. Sau khi chạy 100% ổn định 30 ngày, có thể lưu trữ handler v1 theo quy trình trong slide.
