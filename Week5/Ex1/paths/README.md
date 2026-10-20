Danh sách 18 URL endpoints được ánh xạ trực tiếp từ các thực thể và quan hệ trong ER Diagram:

| STT | HTTP Method | Endpoint URI | Mô tả nghiệp vụ |
| :---: | :--- | :--- | :--- |
| **1** | `GET` | `/hotels` | Lấy danh sách tất cả các khách sạn |
| **2** | `POST` | `/hotels` | Tạo/thêm một khách sạn mới |
| **3** | `GET` | `/hotels/{hotelId}` | Lấy thông tin một khách sạn |
| **4** | `PATCH` | `/hotels/{hotelId}` | Cập nhật thông tin một khách sạn |
| **5** | `GET` | `/hotels/{hotelId}/room-types` | Lấy danh sách các hạng phòng thuộc một khách sạn |
| **6** | `POST` | `/hotels/{hotelId}/room-types` | Thêm hạng phòng mới cho khách sạn |
| **7** | `GET` | `/room-types/{roomTypeId}` | Lấy chi tiết thông tin một hạng phòng |
| **8** | `GET` | `/room-types/{roomTypeId}/rooms` | Lấy danh sách các phòng trong 1 hạng phòng |
| **9** | `POST` | `/customers` | Tạo mới hồ sơ khách hàng |
| **10** | `GET` | `/customers/{customerId}` | Lấy thông tin chi tiết của một khách hàng |
| **11** | `GET` | `/customers/{customerId}/bookings` | Lấy danh sách đơn đặt phòng của một khách hàng |
| **12** | `POST` | `/bookings` | Tạo mới một đơn đặt phòng |
| **13** | `GET` | `/bookings/{bookingId}` | Lấy thông tin chi tiết một đơn đặt phòng |
| **14** | `PATCH` | `/bookings/{bookingId}` | Cập nhật thông tin một đơn đặt phòng |
| **15** | `POST` | `/bookings/{bookingId}/cancellation` | Tạo yêu cầu hủy đơn đặt phòng |
| **16** | `GET` | `/bookings/{bookingId}/payments` | Lấy danh sách các thanh toán của một đơn đặt phòng |
| **17** | `POST` | `/bookings/{bookingId}/payments` | Ghi nhận thanh toán |
| **18** | `GET` | `/bookings/{bookingId}/payments/{paymentId}` | Lấy chi tiết 1 thanh toán của 1 đơn đặt hàng |
