# Lab 4 — Phân tích kết quả

| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | 27 | 0.00% | 4.74 |
| B | 50 | 5 | 60s | 31 | 0.36% | 23.48 |
| C | 200 | 50 | 30s | 60 | 0.52% | 96.93 |

### 1. Kịch bản có p95 cao nhất là gì? Dùng số liệu quan sát để giải thích.

Kịch bản C có p95 cao nhất, đạt **60 ms**, so với 27 ms ở A và 31 ms ở B.

Kịch bản C sử dụng 200 users với spawn rate 50 users/s, tạo tải đồng thời lớn hơn hai kịch bản còn lại. Khi tải tăng, thời gian phản hồi cũng tăng. Average response time của C là 15 ms, trong khi A là 8 ms và B là 9 ms. Tuy nhiên, p95 của C vẫn chỉ ở mức 60 ms.

### 2. Endpoint nào tăng failure rate? Phân biệt lỗi HTTP thực và lỗi đánh dấu trong Locust.

Endpoint `GET /books?year={year}` có các lỗi được ghi nhận:

- Kịch bản A: 0/30 request lỗi (0%).
- Kịch bản B: 5/374 request lỗi (khoảng 1.34%).
- Kịch bản C: 15/726 request lỗi (khoảng 2.07%).

Các endpoint còn lại (`GET /books`, `GET /books/{id}`, `POST /books`) không ghi nhận request lỗi trong cả ba kịch bản.

Các lỗi trên có thông báo `Simulated 500 - injected 1% failure`. Đây là lỗi được chủ động đánh dấu bằng `response.failure()` trong Locust, không phải bằng chứng server Flask thực sự trả về HTTP 500.

Failure rate tổng thể lần lượt là 0%, 0.36% và 0.52% ở A, B và C. Tỷ lệ này tăng khi số lượng request tăng, nhưng cần phân biệt lỗi mô phỏng phía client với lỗi HTTP thực tế từ API.

### 3. Với SLO giả định p95 < 300 ms, kịch bản nào đạt? Nêu giới hạn của phép đo.

Cả ba kịch bản đều đạt SLO giả định p95 < 300 ms:

- A: 27 ms < 300 ms.
- B: 31 ms < 300 ms.
- C: 60 ms < 300 ms.

Như vậy, trong phạm vi phép thử này, cả ba kịch bản đều có p95 thấp hơn ngưỡng SLO.

Tuy nhiên, kết quả chỉ phản ánh môi trường thử nghiệm cục bộ sử dụng SQLite và Flask development server trên máy cá nhân. Kết quả không đủ để khẳng định hệ thống có thể đáp ứng tải tương tự trong môi trường production. Phép đo còn phụ thuộc vào cấu hình máy, dữ liệu thử nghiệm, môi trường chạy và cách tạo tải của Locust.

### 4. Nếu connection pool bị giới hạn ở 5, bạn sẽ kiểm chứng ảnh hưởng như thế nào?

Nếu connection pool chỉ cho phép tối đa 5 kết nối đồng thời, trong khi kịch bản C tạo ra 200 users, các request cần truy cập database có thể phải chờ đến khi một kết nối được giải phóng.

Điều này có thể làm tăng thời gian chờ lấy kết nối, tăng response time và p95; trong trường hợp tải vượt khả năng xử lý trong thời gian dài, request còn có thể timeout hoặc thất bại.

Để kiểm chứng, có thể thực hiện hai lần thử trong cùng điều kiện tải: một lần với pool giới hạn 5 kết nối và một lần với giới hạn lớn hơn. Sau đó so sánh p95, throughput, failure rate và thời gian chờ lấy kết nối. Cần giữ nguyên các yếu tố khác để kết quả có thể so sánh được.

Đây là phân tích giả định về ảnh hưởng của giới hạn connection pool, không phải kết luận rằng môi trường thử nghiệm hiện tại chắc chắn đang sử dụng pool có giới hạn 5.

> Không điền số liệu giả định vào bảng. Không khẳng định hiệu năng production từ SQLite + Flask development server trên máy cá nhân.