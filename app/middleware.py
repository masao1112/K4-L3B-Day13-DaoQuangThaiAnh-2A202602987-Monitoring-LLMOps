from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Xóa sạch contextvars cũ trước khi xử lý request mới để ngăn ngừa rò rỉ dữ liệu (context leakage)
        clear_contextvars()

        # 2. Nhận x-request-id từ header của client gửi lên (nếu có), hoặc sinh ngẫu nhiên theo chuẩn req-<8-char-hex>
        correlation_id = request.headers.get("x-request-id")
        if not correlation_id:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        # 3. Gắn correlation_id vào structlog contextvars để mọi log phát sinh trong luồng xử lý tự động có trường này
        bind_contextvars(correlation_id=correlation_id)

        # Lưu correlation_id vào request.state để các route handler hoặc exception handler downstream có thể truy xuất
        request.state.correlation_id = correlation_id

        # 4. Đo thời gian xử lý toàn bộ request (bắt đầu bấm giờ)
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        # 5. Gắn correlation_id và processing time vào response headers để client/caller dễ dàng truy vết và đo latency
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(duration_ms)

        return response
