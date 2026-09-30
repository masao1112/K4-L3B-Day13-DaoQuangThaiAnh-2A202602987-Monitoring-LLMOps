# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `p95(latency_ms) <= 3000ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng phải chờ lâu hơn để nhận được câu trả lời từ chatbot, gây giảm trải nghiệm người dùng.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel **Latency** để xác nhận P95 và P99 tăng từ thời điểm nào.
  2. Lọc file `data/logs.jsonl` trong khoảng thời gian đó, tìm các log dòng `response_sent` có `latency_ms > 3000` và trích xuất `correlation_id`.
  3. Mở Langfuse tìm trace có `correlation_id` tương ứng, so sánh span `retrieval` và `generation` để xác định bước gây nghẽn.
- Mitigation tạm thời: Nếu do prompt mới làm LLM sinh dài $\to$ rollback prompt về version cũ; nếu do tài liệu retriever $\to$ kiểm tra RAG hoặc scale replica.
- Owner: `student-2A202602987`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `3m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `error_rate <= 2%`
- Điều kiện và thời gian duy trì: `error_rate > 2%` liên tục trong 3 phút
- Ảnh hưởng tới người dùng: Nhiều người dùng nhận mã lỗi HTTP 500 hoặc thông báo không thể hoàn thành yêu cầu, ảnh hưởng trực tiếp đến tính khả dụng của dịch vụ.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel **Errors** để kiểm tra tỷ lệ lỗi và số lượng request thất bại.
  2. Lọc file `data/logs.jsonl` tìm các sự kiện `request_failed`, xem `error_type` và `correlation_id`.
  3. Kiểm tra trace trên Langfuse để xem exception phát sinh tại API, RAG hay LLM call.
- Mitigation tạm thời: Khởi động lại service nếu rò rỉ bộ nhớ/deadlock, chuyển hướng sang fallback model hoặc tắt feature bị lỗi tạm thời.
- Owner: `student-2A202602987`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `retrieval_success_rate >= 90%`
- Điều kiện và thời gian duy trì: `retrieval_success_rate < 90%` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Mô hình không nhận được tài liệu liên quan, dẫn đến câu trả lời hallucinate hoặc chất lượng phản hồi suy giảm (quality score thấp).
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel **Errors / Quality** để theo dõi tỷ lệ `retrieval_success` và `quality_score`.
  2. Lọc file `data/logs.jsonl` tìm các log có `tool_name="retrieval"` và `tool_success=False`.
  3. Kiểm tra trace trên Langfuse tại span `retrieval` xem vector database hoặc search index có timeout hoặc trả về rỗng không.
- Mitigation tạm thời: Khởi động lại kết nối vector store/retriever, kích hoạt fallback knowledge base tĩnh.
- Owner: `student-2A202602987`
