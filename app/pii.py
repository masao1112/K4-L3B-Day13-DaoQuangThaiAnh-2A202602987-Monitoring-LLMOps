from __future__ import annotations

import hashlib
import re

# Module xử lý làm sạch dữ liệu nhạy cảm (PII - Personally Identifiable Information)
# Bảo đảm các thông tin như email, điện thoại, CCCD, thẻ thanh toán được che dấu trước khi ghi log hoặc gửi tới trace.

# Danh sách regex patterns nhận diện các định dạng PII thường gặp tại Việt Nam:
PII_PATTERNS: dict[str, str] = {
    # Địa chỉ email: username@domain.ext
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    # Số điện thoại Việt Nam: hỗ trợ đầu số 0 hoặc +84, cùng các định dạng phân cách khoảng trắng, dấu gạch nối, dấu chấm
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    # Căn cước công dân (CCCD): dãy 12 chữ số
    "cccd": r"\b\d{12}\b",
    # Số thẻ tín dụng / thanh toán: 16 chữ số chia thành 4 nhóm
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    # Hộ chiếu Việt Nam: 1 chữ cái in hoa theo sau bởi 7-8 chữ số
    "passport_vn": r"\b[A-Z][0-9]{7,8}\b",
}


def scrub_text(text: str) -> str:
    """Thay thế các chuỗi khớp với pattern PII bằng nhãn [REDACTED_<LOẠI>] tương ứng.
    
    Đảm bảo văn bản an toàn không chứa dữ liệu cá nhân thô trước khi lưu trữ hoặc render.
    """
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    """Làm sạch PII và rút gọn độ dài text để làm preview an toàn trong log."""
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    """Băm định danh người dùng bằng SHA-256 (lấy 12 ký tự hex đầu).
    
    Giúp che giấu user_id thật nhưng vẫn giữ tính liên kết (pseudonymization) khi quan sát request.
    """
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]

