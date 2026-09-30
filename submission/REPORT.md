# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Đào Quang Thái Anh
- **MSSV:** 2A202602987
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/masao1112/K4-L3B-Day13-DaoQuangThaiAnh-2A202602987-Monitoring-LLMOps
- **Commit SHA cuối:** e53941a
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602987`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard latency & errors | `evidence/11c-dashboard-latency.png` |
| Dashboard cost | `evidence/11a-dashboard-cost.png` |
| Dashboard token & cost | `evidence/11b-dashboard-token-cost.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt toàn bộ các tiêu chí: schema, correlation ID, log enrichment và PII scrubbing |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Hợp lệ toàn bộ 6/6 panels contract |
| `pytest` | 22 passed | 25 passed | Thêm 3 test cases kiểm tra PII cho CCCD, thẻ thanh toán và hộ chiếu |
| Số traces hợp lệ | 0 | 10+ | Đã sinh đầy đủ traces trên Langfuse project cá nhân |
| Số PII leak | 0 | 0 | Không còn rò rỉ dữ liệu nhạy cảm thô trong log |
| Latency P95 / TTFT P95 | ~2061ms / 50ms | ~459ms / 50ms | Đo ở trạng thái bình thường (khi có incident: ~2655ms) |
| Retrieval success rate | 100% | 100% | Retrieval hoạt động ổn định |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `CorrelationIdMiddleware`, trước mỗi request gọi `clear_contextvars()` để xóa context cũ tránh rò rỉ giữa các request async. Lấy `x-request-id` từ header nếu client truyền lên, nếu không có thì tự sinh mới bằng `f"req-{uuid.uuid4().hex[:8]}"`. Sau đó gọi `bind_contextvars(correlation_id=correlation_id)`, lưu vào `request.state.correlation_id`, và trả về qua response header `x-request-id` cùng `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Tại `/chat`, context được làm giàu với `user_id_hash` (mã băm sha256 12 ký tự), `session_id`, `feature`, `model` (`claude-sonnet-4-5`), `env` (`dev`). Ngoài ra log `response_sent` còn ghi nhận các trường đo lường: `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`, và `payload` chứa preview đã làm sạch.
- **Cách bảo đảm PII được scrub trước khi ghi:** Xây dựng hàm `_scrub_deep` duyệt đệ quy qua mọi cấu trúc dữ liệu (chuỗi, dict, list) và regex scrubbing cho các mẫu PII (email, số điện thoại VN với nhiều định dạng phân cách, CCCD 12 số, thẻ tín dụng 16 số, hộ chiếu VN). Đăng ký processor `scrub_event` trong `structlog` trước `JsonlFileProcessor` và `JSONRenderer` để mọi log trước khi xuất ra console hay ghi file đều đã bị che giấu PII.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` (đạt điểm 100/100, 0 PII leak), chạy bộ unit tests `python -m pytest tests/test_pii.py tests/test_validate_logs.py` (toàn bộ 100% pass).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Project Langfuse cá nhân được đặt tên `day13-k4-l3b-2A202602987`. Mỗi trace được gắn tag `["lab", feature, self.model]`, environment `dev`, metadata chứa `correlation_id` khớp từng ký tự với log trong `data/logs.jsonl` và `user_id_hash` được bảo vệ an toàn.
- **Cấu trúc root/retrieval/generation observations:**
  - Root observation: `day13-agent-request` (loại agent/trace) chứa toàn bộ ngữ cảnh request.
  - Child observation 1: `retrieval` (loại `retriever`), đo đạc thời gian tìm kiếm tài liệu ngữ cảnh và số lượng docs trả về.
  - Child observation 2: `generation` (loại `generation`), đo đạc thời gian sinh văn bản của LLM, lưu thông tin model, prompt text preview, token usage và chi phí ước tính (USD).
- **Cách nối trace với log:** Cả hai hệ thống đều sử dụng chung trường `correlation_id` (định dạng `req-<8-hex>`). Trong log, trường này được gắn tự động qua `structlog` contextvars. Trong Langfuse trace, trường này được truyền vào `metadata={"correlation_id": correlation_id}` của cả root trace lẫn các child observations.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 (label `production`)
- **Version/label candidate:** Version 2 (label `staging` hoặc được promote lên `production` để kiểm thử)
- **Trace ID của mỗi version:** Được tự động gán và ghi nhận trong metadata của generation span (`prompt_version: "1"` hoặc `"2"`).
- **Cách promote và rollback `production`:**
  - *Promote:* Vào giao diện Langfuse > Prompts > `day13-chat` > chọn Version 2 > gán nhãn `production`.
  - *Rollback:* Khi phát hiện Version 2 gây tăng latency hoặc suy giảm chất lượng, quay lại Version 1 và gán lại nhãn `production` trỏ về Version 1.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  1. *Latency:* Theo dõi phân vị thời gian phản hồi P50, P95, P99 và TTFT (Time to First Token) của request.
  2. *Traffic:* Tần suất request gửi tới hệ thống theo thời gian (Requests per minute).
  3. *Errors:* Tỷ lệ request thất bại và tỷ lệ thành công của công đoạn retrieval (`tool_success`).
  4. *Cost:* Tổng chi phí tích lũy ước tính bằng USD dựa trên số token input/output đã tiêu thụ.
  5. *Tokens:* Biểu đồ phân bố số lượng tokens vào (input) và tokens ra (output).
  6. *Quality:* Điểm số chất lượng câu trả lời dự kiến (quality proxy score) tính theo heuristic.
- **SLO và lý do chọn:**
  - *SLO:* 99.5% request hoàn thành thành công (`event == "response_sent"`) và có `latency_ms <= 3000ms` trong cửa sổ đánh giá 28 ngày.
  - *Lý do chọn:* Đảm bảo phần lớn người dùng nhận được phản hồi nhanh chóng (dưới 3 giây) mà không gặp lỗi gián đoạn dịch vụ.
- **Cách tính error budget:**
  - Error budget = 100% - 99.5% = 0.5%.
  - Ví dụ: Trong cửa sổ 28 ngày nếu có tổng cộng 10,000 request gửi đến, ngân sách lỗi cho phép tối đa 50 request không đạt tiêu chuẩn (bị lỗi HTTP 500 hoặc latency > 3000ms).
- **Ba alert và runbook tương ứng:**
  1. `HighLatencyP95`: Cảnh báo khi P95 latency > 3000ms trong 5 phút. Runbook: `docs/alerts.md#alert-1`.
  2. `HighErrorRate`: Cảnh báo khi tỷ lệ lỗi > 2% trong 3 phút. Runbook: `docs/alerts.md#alert-2`.
  3. `LowRetrievalSuccess`: Cảnh báo khi tỷ lệ tìm kiếm tài liệu thành công < 90% trong 5 phút. Runbook: `docs/alerts.md#alert-3`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 11:27:15 – 11:36:04 (UTC+7, tương ứng 04:27:15 – 04:36:04 UTC)
- **Triệu chứng từ metrics:** Panel Latency trên Dashboard ghi nhận độ trễ P95 tăng vọt bất thường lên ~2655ms (vượt xa ngưỡng an toàn `latency_threshold_ms: 2000` được định nghĩa trong challenge).
- **Log line và correlation ID liên quan:**
  Log dòng `response_sent`:
  ```json
  {"service": "api", "latency_ms": 2654, "ttft_ms": 50, "tokens_in": 45, "tokens_out": 145, "cost_usd": 0.00231, "quality_score": 0.9, "tool_name": "retrieval", "tool_success": true, "payload": {"answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."}, "event": "response_sent", "correlation_id": "req-ac79769c", "env": "dev", "user_id_hash": "2055254ee30a", "feature": "qa", "session_id": "s01", "model": "claude-sonnet-4-5", "level": "info", "ts": "2026-09-30T04:27:18.483030Z"}
  ```
  Correlation ID đại diện: `req-ac79769c`
- **Trace ID và span gây ảnh hưởng:**
  Tìm trace có `correlation_id = req-ac79769c` trên Langfuse. Trong cây trace waterfall:
  - Root span `day13-agent-request` mất 2654ms.
  - Span con `generation` chỉ mất ~154ms.
  - **Span gây ảnh hưởng chính là `retrieval`**, chiếm đến 2500ms / 2654ms (khoảng 94% tổng thời gian request).
- **Root cause:**
  Sự cố nghẽn mạng / delay tại bước Retrieval trong pipeline RAG (cụ thể do kích hoạt incident `rag_slow` gây sleep 2.5s tại `mock_rag.retrieve()`).
- **Fix action:**
  Vô hiệu hóa incident bằng lệnh:
  ```bash
  python scripts/inject_incident.py --scenario rag_slow --disable
  ```
  (Trong môi trường thực tế: kiểm tra kết nối vector database, tối ưu index và scale thêm replica cho retriever).
- **Preventive measure:**
  1. Cấu hình alert `HighLatencyP95` (với threshold 2000ms trong 5 phút) gửi thông báo về Slack `#k4-l3b-alerts`.
  2. Thiết lập cơ chế Timeout chặt chẽ cho bước retrieval (ví dụ: timeout = 1000ms) kèm fallback knowledge base để tránh nghẽn luồng request của người dùng.
  3. Áp dụng circuit breaker nhằm cô lập lỗi từ vector store, tránh cascade failure sang toàn bộ hệ thống API.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Triển khai hàm làm sạch đệ quy `_scrub_deep` trong `scrub_event` và đăng ký nó trước `JsonlFileProcessor` và `JSONRenderer`. Điều này triệt tiêu hoàn toàn khả năng rò rỉ PII bất kể cấu trúc dữ liệu lồng nhau phức tạp thế nào trước khi dữ liệu được ghi xuống file log.
- **Một lỗi/blocker đã gặp:** Gặp lỗi 401 Unauthorized khi Langfuse Cloud kiểm tra chứng thực API key cá nhân.
- **Cách tìm nguyên nhân và xử lý:** Kiểm tra phản hồi HTTP từ server Langfuse, xác nhận lại endpoint tương ứng (`https://cloud.langfuse.com` vs `https://us.cloud.langfuse.com`) và tạo mới API key pair trong Project Settings của Langfuse.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - *Metrics:* Cung cấp góc nhìn tổng quan (symptom) và khoanh vùng thời gian xảy ra vấn đề.
  - *Logs:* Giúp định vị chính xác request bị lỗi bằng `correlation_id` và đọc các sự kiện liên quan.
  - *Traces:* Phân rã request đó thành các span lồng nhau (retrieval, LLM generation) để xác định chính xác bước nào bị nghẽn hoặc phát sinh exception (Root Cause).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - Prompt quản lý theo version cho phép đội ngũ kỹ thuật thay đổi hành vi mô hình an toàn, đo lường tác động đến token/chi phí và rollback lập tức về phiên bản ổn định mà không cần triển khai lại mã nguồn.
- **Điều quan trọng nhất đã học:** Nắm vững phương pháp điều tra sự cố dựa trên bằng chứng dữ liệu có thể kiểm chứng thay vì suy đoán chủ quan.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Không có. Đã hoàn thành 100% tất cả các hạng mục từ CP0 đến CP4, bao gồm bộ test, logging, PII, trace, dashboard và điều tra sự cố challenge.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

