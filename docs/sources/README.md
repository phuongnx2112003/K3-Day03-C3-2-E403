# Nguồn dữ liệu học vụ VinUni

Ngày kiểm tra/tải: 2026-07-28

## Bản đã tải về project

| Nguồn | File cục bộ | Nội dung sử dụng |
|---|---|---|
| [Academic Regulations for Full-Time Undergraduate Programs](https://policy.vinuni.edu.vn/all-policies/academic-regulations-for-full-time-undergraduate-programs/) | [vinuni-academic-regulations.pdf](vinuni-academic-regulations.pdf) | Credit, course registration, prerequisite, study load và add/drop. |
| [Computer Science curriculum](https://cecs.vinuni.edu.vn/undergraduate/computer-science/) | [vinuni-computer-science-curriculum.pdf](vinuni-computer-science-curriculum.pdf) | Cấu trúc chương trình, tổng 120/135 credits và prerequisite theo môn. |

## Nguồn trực tuyến cần truy cập

- [VinUni Registrar Policy & Regulations](https://registrar.vinuni.edu.vn/academics/policy-regulations/): danh mục chính sách, academic catalog, lịch học và dịch vụ Registrar.
- [Student Gateway](https://vinuni.edu.vn/student-gateway/): liên kết tới academic calendar, academic catalog, registry services và course schedule/SIS.

Hai trang HTML trên vẫn được giữ dưới dạng nguồn chính thức trực tuyến vì server từ chối tải bản HTML tự động (HTTP 403); không nên coi bản snapshot cục bộ là dữ liệu thay thế cho trang chính thức.

## Một số điểm dữ liệu chính

- Academic Regulations quy định 1 credit tương đương khoảng 50 giờ học tổng cộng; lecture-based course thường khoảng 15 contact hours và khuyến nghị ít nhất 30 giờ tự học cho mỗi credit.
- Full-time undergraduate cần tối thiểu 12 credits trong regular semester; mức tải thông thường và overload phụ thuộc standing/approval.
- Sinh viên phải đáp ứng prerequisite; ngoại lệ cần Program Director phê duyệt.
- Computer Science có lựa chọn 120 credits cho single major hoặc 135 credits khi kết hợp major và minor.

Khi dữ liệu trên trang chính thức thay đổi, cần tải lại các PDF và cập nhật ngày kiểm tra trước khi dùng làm căn cứ cho quyết định học vụ.

## Cách Agent truy xuất tài liệu

Tool `search_official_sources(query)` trong `src/tools.py` đọc và cache nội dung PDF, sau đó trả về đoạn trích cùng tên tài liệu và số trang. ReAct Agent gọi tool này khi cần xác minh credit, study load, prerequisite hoặc cấu trúc chương trình. Hai nguồn Registrar và Student Gateway vẫn cần truy cập online/SIS vì không có bản snapshot cục bộ.
