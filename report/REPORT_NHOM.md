# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học bổng và hỗ trợ tài chính dành cho người học tại Trường Đại học Khoa học và Công nghệ Hà Nội (USTH).

**Tại sao nhóm chọn chủ đề này?**
> Bộ tài liệu tập hợp các quy định, tiêu chí, giá trị, hồ sơ, quy trình và thời hạn học bổng từ các nguồn công khai của USTH. Phạm vi này phù hợp để xây dựng hệ thống truy xuất vì người học thường cần đối chiếu thông tin cụ thể giữa nhiều loại học bổng và năm học khác nhau.

**Mô tả corpus:** Corpus gồm đúng 8 tài liệu Markdown: 5 tài liệu tiếng Anh và 3 tài liệu tiếng Việt, được lấy ngày 2026-09-19. Nội dung bao phủ quy định chung, thông báo nộp hồ sơ, quy trình, học bổng Vallet, học bổng cho sinh viên hiện tại, chương trình Green Tech, hỗ trợ tài chính và các đợt đang hiển thị trên cổng học bổng. Nguồn tuyển sinh tiến sĩ bị chặn bởi `robots.txt` không được đưa vào corpus.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự (không tính frontmatter) | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Regulations on Scholarship for USTH Students | https://usth.edu.vn/en/regulations-on-scholarship-for-usth-students-11708/ | 2026-09-19 / 177-QD-DHKHCNHN-2026 | 1328 | `audience: student`; `department: student-affairs`; `category: scholarship-regulation`; `language: en` |
| 2 | Scholarship Application Submission 2026-2027 Wave 1 | https://usth.edu.vn/en/announcement-on-scholarship-application-submission-academic-year-2026-2027-wave-1-12694/ | 2026-09-19 / 2026-2027 | 3213 | `audience: student`; `department: student-affairs`; `category: application`; `language: en` |
| 3 | Procedures for Scholarships and Financial Aids Support | https://usth.edu.vn/en/procedures-for-scholarships-and-financial-aids-support-3632/ | 2026-09-19 / not-stated | 1173 | `audience: all`; `department: student-affairs`; `category: procedure`; `language: en` |
| 4 | Vallet Scholarship Program 2026 for Northern Students | https://usth.edu.vn/thong-bao-trien-khai-chuong-trinh-hoc-bong-vallet-nam-2026-danh-cho-sinh-vien-khu-vuc-mien-bac-31432/ | 2026-09-19 / 01-2026-TB-HBSVMB | 6001 | `audience: student`; `department: student-affairs`; `category: external-scholarship`; `language: vi` |
| 5 | Scholarship Application for Current Vietnamese Students 2025-2026 | https://usth.edu.vn/tiep-nhan-ho-so-dang-ky-hoc-bong-nam-hoc-2025-2026-danh-cho-sinh-vien-hoc-vien-viet-nam-dang-hoc-tai-truong-26801/ | 2026-09-19 / 536-QD-KHCN-2025 | 4393 | `audience: student`; `department: student-affairs`; `category: current-student-scholarship`; `language: vi` |
| 6 | Green Tech Scholarship and Internship 2026 | https://usth.edu.vn/en/green-tech-scholarship-internship-2026-11897/ | 2026-09-19 / not-stated | 861 | `audience: student`; `department: student-affairs`; `category: external-scholarship`; `language: en` |
| 7 | Financial Aid for Students in Difficult Circumstances 2024-2025 | https://usth.edu.vn/en/financial-aid-award-ceremony-for-students-in-difficult-circumstances-academic-year-2024-2025-12301/ | 2026-09-19 / 2024-2025 | 4635 | `audience: student`; `department: student-affairs`; `category: financial-aid`; `language: en` |
| 8 | USTH Student Scholarship Portal 2026-2027 | https://erp.usth.edu.vn/students | 2026-09-19 / 2026-2027 | 472 | `audience: student`; `department: student-affairs`; `category: scholarship-portal`; `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated` khi nguồn không nêu phiên bản) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `usth-scholarship-regulation-2026` | Định danh duy nhất tài liệu và đối chiếu kết quả với tệp nguồn. |
| `title` | string | `Regulations on Scholarship for USTH Students` | Hiển thị và xếp hạng kết quả theo tên tài liệu. |
| `source_url` | URL | `https://usth.edu.vn/en/regulations-on-scholarship-for-usth-students-11708/` | Truy vết và kiểm chứng nội dung từ nguồn gốc. |
| `retrieved_at` | date (`YYYY-MM-DD`) | `2026-09-19` | Xác định thời điểm thu thập khi đánh giá độ mới của dữ liệu. |
| `document_version` | string | `177-QD-DHKHCNHN-2026` | Phân biệt quy định theo số hiệu/phiên bản; dùng `not-stated` khi nguồn không nêu. |
| `audience` | enum (`student`, `faculty`, `staff`, `all`) | `student` | Cho phép lọc tài liệu theo đối tượng. |
| `department` | string | `student-affairs` | Giới hạn truy xuất theo đơn vị phụ trách. |
| `category` | string | `application` | Lọc theo loại nội dung như thông báo nộp hồ sơ, quy định hay quy trình. |
| `language` | string | `en` | Lọc theo ngôn ngữ của tài liệu. |
| `license_or_permission` | string | `public-source` | Ghi nhận căn cứ sử dụng và hỗ trợ kiểm tra quản trị dữ liệu. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
