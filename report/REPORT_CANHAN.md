# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Nguyễn Trâm Anh  
**Nhóm:** AuraFarming  
**Lớp:** L3A  
**Ngày hoàn thiện:** 19/09/2026

> Báo cáo này trình bày phần triển khai và thực nghiệm cá nhân. Các kết luận định lượng chỉ sử dụng đầu ra kiểm thử và benchmark đã chạy trên repo; không nội suy thêm số liệu.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự cosine (Bài tập 1.1)

Cosine similarity đo mức độ cùng hướng giữa hai vector embedding, với công thức:

\[
\operatorname{cos}(a,b)=\frac{a\cdot b}{\lVert a\rVert\lVert b\rVert}.
\]

Giá trị cao cho biết hai biểu diễn gần nhau về hướng và thường phản ánh nội dung/ngữ nghĩa gần nhau; giá trị thấp cho biết hai văn bản ít liên quan trong không gian embedding. Đây là tín hiệu xếp hạng, không tự nó chứng minh câu trả lời đúng về mặt dữ kiện.

**Ví dụ có độ tương tự cao**

- Câu A: “Hạn nộp hồ sơ là ngày 23 tháng 3 năm 2026.”
- Câu B: “Ứng viên phải gửi đơn trước ngày 23/03/2026.”
- Hai câu diễn đạt cùng một sự kiện và cùng mốc thời gian bằng hai cách viết.

**Ví dụ có độ tương tự thấp**

- Câu A: “Quy trình xét học bổng gồm ba bước.”
- Câu B: “Thư viện mở cửa từ thứ Hai đến thứ Sáu.”
- Hai câu thuộc hai chủ đề và hai nhu cầu thông tin khác nhau.

Cosine similarity phù hợp với text embedding vì tập trung vào **hướng** của vector, tức mẫu đặc trưng ngữ nghĩa tương đối, thay vì bị chi phối trực tiếp bởi độ lớn vector như khoảng cách Euclid. Trong benchmark, `LocalEmbedder` còn chuẩn hóa embedding (`normalize_embeddings=True`), nên tích vô hướng dùng trong store tương đương cosine similarity và có thể dùng trực tiếp để xếp hạng.

### Bài toán chunking (Bài tập 1.2)

Với tài liệu dài \(N=10{,}000\), `chunk_size=500`, `overlap=50`, bước trượt là:

\[
s=500-50=450.
\]

Số chunk theo đúng cửa sổ trượt trong `FixedSizeChunker` là:

\[
1+\left\lceil\frac{N-500}{450}\right\rceil
=1+\left\lceil\frac{9{,}500}{450}\right\rceil
=23.
\]

Nếu tăng overlap lên 100, bước trượt còn 400 và số chunk là:

\[
1+\left\lceil\frac{10{,}000-500}{400}\right\rceil=25.
\]

Overlap lớn hơn tạo thêm hai chunk trong ví dụ này và lặp lại nhiều ngữ cảnh hơn giữa các cửa sổ. Điều đó có thể bảo toàn thông tin nằm gần biên chunk, nhưng đồng thời tăng số vector phải lưu/tìm và có thể làm top-k chứa các đoạn gần trùng nhau; vì vậy overlap cần được kiểm chứng bằng benchmark thay vì chọn theo trực giác.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chunking

**`SentenceChunker.chunk`**

Tôi tách câu bằng regex `(?<=[.!?])[ \t]+|(?<=\.)\n+`: nhánh đầu nhận diện khoảng trắng sau `.`, `!`, `?`, nhánh sau nhận diện xuống dòng sau dấu chấm. Các câu được `strip`, phần rỗng bị loại, rồi được gom tối đa `max_sentences_per_chunk`; constructor chặn giá trị không hợp lệ bằng `max(1, ...)`. Văn bản rỗng trả về danh sách rỗng và đoạn cuối vẫn được giữ khi số câu không chia hết.

**`RecursiveChunker.chunk` / `_split`**

Thuật toán thử các separator theo thứ tự ưu tiên `"\n\n" → "\n" → ". " → " " → ""`, nhờ đó ưu tiên ranh giới cấu trúc lớn trước. Base case trả ngay đoạn không vượt `chunk_size`; nếu không còn separator hoặc gặp separator rỗng, thuật toán cắt cứng theo kích thước để bảo đảm kết thúc. Các mảnh quá dài tiếp tục được tách bằng separator kế tiếp, sau đó các mảnh ngắn được gộp lại miễn tổng độ dài không vượt giới hạn.

**`FixedSizeChunker(500, 50)` dùng cho benchmark cá nhân**

Tôi dùng cửa sổ trượt 500 ký tự và overlap 50 như một **controlled baseline**: quy tắc biên cố định, số chunk dự đoán được và chỉ có hai tham số cần kiểm soát. Đây cũng là cấu hình được chọn từ thực nghiệm có kiểm soát trên cùng corpus, cùng 5 query, cùng embedder và cùng `top_k=3`: `500/50 → 4/5`, `500/100 → 3/5`, `400/50 → 2/5`. Vì chỉ thay đổi `chunk_size/overlap`, kết quả hỗ trợ việc quy sự khác biệt cho cấu hình chunking thay vì cho corpus hay mô hình embedding.

### Lớp `EmbeddingStore`

**`add_documents` + `search`**

Mỗi `Document` được chuyển thành record gồm `id`, `content`, bản sao `metadata`, embedding và `doc_id` mặc định lấy từ phần trước dấu `#`. Store in-memory giúp hành vi nhất quán giữa các máy. Khi tìm kiếm, query được embed một lần, tính tích vô hướng với từng embedding đã lưu, sắp giảm dần theo `score` và lấy `top_k`. Với embedding benchmark đã chuẩn hóa, phép tính này chính là cosine ranking.

**`search_with_filter` + `delete_document`**

`search_with_filter` lọc **trước khi xếp hạng**: một record chỉ vào candidate set khi mọi cặp khóa–giá trị trong `metadata_filter` khớp chính xác, rồi mới chạy cùng pipeline similarity search. Cách này làm rõ vai trò của metadata như ràng buộc phạm vi, không phải một điểm cộng mơ hồ vào semantic score. `delete_document` loại toàn bộ record có `metadata.doc_id` tương ứng và trả `True` khi kích thước store thực sự giảm, nên xóa đúng ở cấp tài liệu dù một tài liệu có nhiều chunk.

### Tác tử `KnowledgeBaseAgent.answer`

Agent thực hiện đúng chuỗi RAG: retrieve top-k, ghép từng chunk với số tham chiếu `[1]`, `[2]`, `[3]` và nguồn ưu tiên `source_url → source → doc_id → id`, rồi inject toàn bộ context vào prompt. Prompt yêu cầu chỉ trả lời từ context, trích nguồn bằng số trong ngoặc vuông và nói rõ khi context không chứa đáp án. Nhờ vậy có thể đối chiếu câu trả lời với chunk nguồn và hạn chế sinh nội dung không được grounding; nếu store không trả kết quả, agent dừng sớm bằng thông báo không tìm thấy thông tin.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Checkpoint 3:

```text
23 passed, 19 deselected
```

Kiểm thử toàn bộ được chạy bằng `pytest tests/ -q`:

```text
..........................................                               [100%]
42 passed in 0.08s
```

**Số lượng bài test vượt qua:** **42 / 42**.

Phạm vi kiểm thử bao phủ ba chunker, cosine similarity (gồm zero vector), thống kê comparator, thêm/tìm kiếm/lọc/xóa trong vector store và luồng trả lời của agent. Hai mốc trên phân biệt rõ checkpoint chọn lọc và lần chạy toàn bộ test suite.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Năm cặp dưới đây dùng chính **query và top-1 chunk** của benchmark. Cột “Dự đoán” là giả thuyết định tính trước khi đối chiếu thứ hạng; cột “Điểm thực tế” lấy nguyên từ `ket_qua_benchmark.txt`, được sinh bằng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

| Cặp | Câu A / query | Câu B / nội dung top-1 (tóm tắt) | Dự đoán | Điểm thực tế | Đối chiếu |
|---:|---|---|---|---:|---|
| 1 | Số suất, giá trị và thời hạn Green Tech 2026 | Green Tech: 04 suất, 18.000.000 đồng / 6 tháng | Cao nhất | 0.803126 | Phù hợp |
| 2 | Hạn nộp và thời điểm bắt đầu Green Tech 2026 | Chunk Green Tech chứa phần giới thiệu, giá trị và eligibility; mốc ngày nằm ở chunk kế tiếp | Cao | 0.727291 | Top-1 đúng tài liệu; evidence chi tiết ở rank 2 |
| 3 | Ba bước xét học bổng và hỗ trợ tài chính | “Procedures… followed 3 steps”, mở đầu Step 1 và Step 2 | Cao | 0.711634 | Phù hợp; top-3 bao phủ đủ ba bước |
| 4 | Quỹ 2026–2027 và nhóm người học | Quỹ 16 tỷ đồng cho undergraduate, master và doctoral | Cao | 0.711597 | Phù hợp |
| 5 | Đối tượng áp dụng quy định học bổng 2026 | Portal 2026–2027 liệt kê các loại học bổng và đối tượng | Trung bình | 0.748432 | Score cao nhưng chưa đồng nghĩa đúng gold evidence |

Kết quả đáng chú ý nhất là cặp 5 có score top-1 cao thứ hai dù top-3 chưa chứa đúng đoạn quy định nêu hai nhóm “Vietnamese students” và “international students”. Điều này cho thấy embedding nhận diện tốt trường nghĩa *học bổng–đối tượng–2026*, nhưng semantic proximity không thay thế kiểm chứng dữ kiện. Vì vậy đánh giá retrieval phải dùng gold evidence/top-k relevance, không chỉ dùng score.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### 5.1 Thiết lập có thể tái lập

- Corpus: 8 tài liệu Markdown trong `data/scholarship/`, metadata được đọc từ frontmatter; mỗi chunk giữ `doc_id`, `source_file`, `source_url`, `audience` và `chunk_index`.
- Chunker: `FixedSizeChunker(chunk_size=500, overlap=50)`.
- Embedder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, chuẩn hóa vector.
- Store/ranking: in-memory `EmbeddingStore`, tích vô hướng trên vector chuẩn hóa.
- Evaluation: cùng 5 query/gold answer của nhóm, `top_k=3`; Q5 dùng `metadata_filter={"audience":"student"}`.
- Artifact kết quả: `ket_qua_benchmark.txt`; embedding được cache theo tên backend và SHA-256 nội dung để lần chạy lại dùng đúng vector đã tạo.

### 5.2 Evidence theo từng query

| # | Query (rút gọn) | Top-1 truy xuất và score | Evidence/gold trong top-3 | Agent answer được grounding từ context |
|---:|---|---|---|---|
| 1 | Green Tech: số suất, giá trị, thời hạn | `usth-green-tech-scholarship-2026#0` — **0.803126** | **Có, rank 1**: 04 suất; 18.000.000 VND / 6 tháng | 4 suất, giá trị 18 triệu đồng trong 6 tháng |
| 2 | Green Tech: hạn nộp và bắt đầu | `usth-green-tech-scholarship-2026#0` — **0.727291** | **Có, rank 2** (`#1`): deadline 23/03/2026; dự kiến bắt đầu 04/2026 | Hạn nộp 23/03/2026, dự kiến bắt đầu tháng 04/2026 |
| 3 | Quy trình xét học bổng/hỗ trợ tài chính | `usth-scholarship-procedure#0` — **0.711634** | **Có**: rank 1 chứa mở đầu quy trình, Step 1 và Step 2; rank 3 (`#1`) tiếp nối và chứa Step 3 | Công bố/nhận hồ sơ → lập danh sách, hội đồng và quyết định → công bố danh sách nhận hỗ trợ |
| 4 | Quỹ 2026–2027 và nhóm người học | `usth-scholarship-application-2026#0` — **0.711597** | **Có, rank 1**: 16 tỷ VND; undergraduate, master, doctoral | Quỹ dự kiến 16 tỷ đồng cho sinh viên đại học, học viên cao học và nghiên cứu sinh |
| 5 | Đối tượng áp dụng quy định học bổng 2026 | `usth-scholarship-portal-2026-2027#0` — **0.748432** | Top-3 nói về đối tượng sinh viên/học viên, nhưng **chưa chứa đúng gold evidence** “Vietnamese students” và “international students” | Không khẳng định hai nhóm từ context hiện có; cần đúng chunk quy định để trả lời có căn cứ |

**Kết quả chính:** **4 / 5 query có gold evidence trong top-3**. Cụ thể, Q1 và Q4 đặt evidence ở rank 1; Q2 đặt evidence chi tiết ở rank 2; Q3 cần đọc kết hợp các chunk rank 1 và rank 3 để bao phủ đủ ba bước. Việc báo cáo ở cấp chunk/rank làm kết quả có thể kiểm chứng và tránh đánh đồng “đúng tài liệu” với “đủ bằng chứng”.

### 5.3 Thí nghiệm tuning có kiểm soát

| Cấu hình (`chunk_size/overlap`) | Query có gold evidence trong top-3 |
|---|---:|
| **500/50** | **4/5** |
| 500/100 | 3/5 |
| 400/50 | 2/5 |

Thiết kế thí nghiệm giữ cố định corpus, cách parse metadata, năm query, gold evidence, embedder, store, `top_k=3` và cách chấm; chỉ thay tham số chunking. So sánh `500/50` với `500/100` cô lập tác động của overlap, còn so sánh `500/50` với `400/50` kiểm tra tác động của kích thước. Trên bộ benchmark này, `500/50` cho độ bao phủ gold evidence cao nhất trong ba cấu hình đã đo: 500 ký tự đủ chứa các cụm dữ kiện liên quan, còn 50 ký tự tạo cầu nối ở biên mà không tăng quá nhiều đoạn gần trùng trong top-3.

### 5.4 Phân tích metadata filter qua Q5

Q5 gọi `search_with_filter(..., metadata_filter={"audience":"student"})`, nghĩa là candidate set được giới hạn theo audience trước semantic ranking. Thử nghiệm A/B giữ nguyên query, embedder, chunking và `top_k`; kết quả **filtered và unfiltered có cùng top-3**. Đây là một quan sát có ý nghĩa: trong corpus hiện tại, ba ứng viên semantic mạnh nhất của Q5 vốn đã có `audience=student`, nên filter xác nhận phạm vi đối tượng nhưng không thay đổi thứ hạng.

Kết quả này không phủ nhận giá trị của metadata. Semantic ranking trả lời “nội dung nào gần query nhất?”, còn metadata filter thực thi ràng buộc “ứng viên nào được phép tham gia?”. Khi corpus mở rộng thêm tài liệu cho `faculty`, `staff` hoặc `all`, cùng bộ lọc có thể thay đổi candidate set; với corpus hiện tại, A/B cho thấy filter không làm giảm recall của top-3 đang quan sát.

### 5.5 Bài học rút ra

Điều quan trọng nhất tôi rút ra là phải đánh giá toàn bộ pipeline bằng thí nghiệm công bằng. Chunking quyết định đơn vị bằng chứng; overlap bảo toàn ngữ cảnh qua biên nhưng cũng thay đổi mật độ chunk; embedding đưa query và chunk vào cùng không gian vector; vector store xếp hạng các ứng viên; metadata áp đặt phạm vi có cấu trúc; và agent chỉ nên tổng hợp điều mà context thực sự hỗ trợ.

`FixedSizeChunker(500, 50)` trong bài này là baseline được kiểm chứng thực nghiệm, không phải lựa chọn dựa trên độ tiện dụng. Cùng lúc, Q2 và Q3 cho thấy vì sao không nên chỉ nhìn top-1: bằng chứng có thể nằm ở rank 2 hoặc được bao phủ qua nhiều chunk trong top-3. Q5 cho thấy score cao vẫn cần kiểm tra gold evidence và A/B filtering; đó là lý do benchmark phải cố định biến kiểm soát, lưu rank/score/chunk ID và đánh giá grounding thay vì suy luận từ cảm giác về kết quả.

---

## Tự đánh giá theo rubric cá nhân

| Tiêu chí | Minh chứng | Điểm tự đánh giá |
|---|---|---:|
| Khởi động | Giải thích cosine, ví dụ và phép tính chunking cho hai overlap | 5 / 5 |
| Hướng tiếp cận | Giải thích implementation trong `src`, edge cases và luồng RAG | 10 / 10 |
| Hoàn thiện code | CP3: 23 passed; toàn bộ: 42/42 passed | 30 / 30 |
| Dự đoán độ tương tự | 5 cặp, dự đoán–điểm thực tế–phản ánh | 5 / 5 |
| Kết quả truy xuất | Thiết lập tái lập, evidence theo rank, tuning và A/B metadata | 10 / 10 |
| **Tổng phần cá nhân** | | **60 / 60** |

Mức tự đánh giá phần retrieval bám đúng minh chứng `4/5` query có gold evidence trong top-3. Các số liệu kiểm thử, score, rank, cấu hình tuning và kết quả A/B trong báo cáo đều là kết quả đã ghi nhận; không bổ sung số liệu ước đoán.
