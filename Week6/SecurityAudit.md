# Security Audit – Social Network API

**Phạm vi:** `app.py` với các endpoint `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh` và `GET /api/v1/posts/{id}`.

## 1. JWT secret mặc định trong source

- **Mức độ:** Critical
- **Vị trí:** `JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-change-this-secret")`
- **Vấn đề/nguy cơ:** Nếu không cấu hình biến môi trường, ứng dụng dùng secret cố định, dễ đoán. Người biết secret có thể tạo JWT giả mạo.
- **Khắc phục:** Bắt buộc sử dụng secret ngẫu nhiên, đủ dài từ secret manager hoặc biến môi trường; từ chối khởi động production nếu vẫn còn secret mặc định; có kế hoạch luân chuyển khóa (key rotation).

## 2. Tài khoản và mật khẩu demo nằm trong mã nguồn

- **Mức độ:** High
- **Vị trí:** Dictionary `users` có tài khoản `ABC123/abc123` và `DEF456/def456`
- **Vấn đề/nguy cơ:** Nếu repository bị công khai hoặc tài khoản demo vẫn tồn tại trên production, người khác có thể đăng nhập bằng thông tin này.
- **Khắc phục:** Xóa tài khoản demo khỏi production; không commit thông tin đăng nhập vào mã nguồn; tạo dữ liệu kiểm thử riêng và quản lý tài khoản qua database.

## 3. Refresh token chỉ được lưu trong RAM

- **Mức độ:** High
- **Vị trí:** Dictionary `refresh_tokens`.
- **Vấn đề/nguy cơ:** Trạng thái token bị mất khi server khởi động lại; không đồng bộ giữa nhiều worker hoặc máy chủ; việc thu hồi phiên không được duy trì lâu dài.
- **Khắc phục:** Lưu hash của refresh token, thời hạn, trạng thái và thông tin phiên trong database hoặc kho lưu trữ phù hợp; hỗ trợ thu hồi phiên đăng nhập.

## 4. Chưa có rate limiting thực tế

- **Mức độ:** High
- **Vị trí:** `/auth/login`, `/auth/refresh`, `/posts/{id}`.
- **Vấn đề/nguy cơ:** Code chưa giới hạn số lượng request. Các response `429` trong thiết kế chưa có logic thực tế để tạo ra, nên hệ thống có thể bị tấn công dò mật khẩu (brute force) hoặc spam request.
- **Khắc phục:** Giới hạn request theo IP và tài khoản, thiết lập ngưỡng riêng cho từng endpoint, trả về mã `429` và header `Retry-After` khi vượt ngưỡng.

## 5. Chưa bắt buộc HTTPS

- **Mức độ:** High
- **Vị trí:** Cau hinh chay Flask va cac endpoint.
- **Vấn đề/nguy cơ:** `app.py` không tự cấu hình TLS. Nếu triển khai qua HTTP mà không có TLS tại reverse proxy, username, password và token có thể bị đọc trên đường truyền.
- **Khắc phục:** Bắt buộc sử dụng HTTPS trong môi trường triển khai; cấu hình TLS tại reverse proxy hoặc load balancer; không gửi token trong URL.

## 6. Nguy cơ lộ thông tin tài khoản qua thông điệp đăng nhập

- **Mức độ:** Medium
- **Vị trí:** `POST /api/v1/auth/login`.
- **Đánh giá:** Code hiện tại trả về cùng một thông điệp `Invalid username or password` cho cả trường hợp username không tồn tại và password sai. Đây là cách làm tốt, nhưng cần duy trì tính nhất quán này ở mọi endpoint đăng nhập.
- **Nguy cơ:** Kẻ tấn công có thể suy đoán tài khoản nào đang tồn tại (user enumeration).
- **Khắc phục:** Sử dụng thông điệp lỗi chung; không trả về password hash hay thông tin nội bộ; không ghi password hoặc token vào log.