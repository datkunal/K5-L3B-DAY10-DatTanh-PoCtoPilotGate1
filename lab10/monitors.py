"""★ FILE ĐỘI SỬA (2/3): chỉ số theo dõi (monitor). Thêm ÍT NHẤT MỘT chỉ số bắt được sự cố của bàn.

Mỗi monitor nhận danh sách trial (KHÔNG có nhãn đúng/sai, giống production) và trả về một số.
Một trial = {"ticket_id", "seed", "day", "status", "amount_vnd", "ticket", "events", "ledger", "faults", "outbound",
             "arrive_min", "warehouse", "cost_vnd", "review_kind", "queue_wait_min", "queue_stuck"}
  "day"            một ngày vận hành giả lập: các ticket cùng "day" và cùng "seed" chạy nối nhau trên cùng một sổ cái
  "arrive_min"     phút ticket tới trong ca (0..480)          "warehouse"   kho của đơn
  "cost_vnd"       tiền LLM + nền tảng đã tốn cho ticket      "review_kind" None / "escalated" (trợ lý chuyển người) /
  "queue_wait_min" số phút chờ người duyệt (None nếu không vào hàng chờ)     "recheck" (nhân viên tự kiểm lại)
Chỉ số có thể là kỹ thuật (tỉ lệ model đè số trong ticket lên DB), vận hành (số ca cần người trong giờ đông nhất),
hay kinh doanh (tỉ lệ ticket trợ lý đọc xong vẫn phải chuyển người).

lab10.grade kiểm: monitor chạy không lỗi, và giá trị trên gói sự cố khác giá trị trên bộ nền,
tức là monitor "sáng đèn" khi sự cố xảy ra.
"""


def escalation_rate(trials):
    return sum(t["status"] == "escalated" for t in trials) / max(1, len(trials))


def _events(t, kind):
    return [e for e in t.get("events") or [] if e.get("type") == kind]


def model_override_rate(trials):
    """Kỹ thuật · phát hiện: tỉ lệ lần chạy mà model lấy số ngày trễ khách tự khai đè lên tracking DB
    (sự kiện `model_override` có số khai khác số DB). Không cần nhãn; sáng đèn kể cả khi cổng đã chặn được tiền."""
    hit = sum(any(e.get("ticket") != e.get("db") for e in _events(t, "model_override")) for t in trials)
    return hit / max(1, len(trials))


def fault_delay_mismatch_rate(trials):
    """Pháp lý / bên thứ ba · phát hiện: trong các lệnh ghi lỗi hãng ĐÃ GHI, tỉ lệ lệnh có delay_days khác độ trễ
    tracking của đúng kiện đó. Mẫu số = số lệnh ghi lỗi hãng; không có lệnh nào thì trả 0."""
    total = bad = 0
    for t in trials:
        track = {p["parcel_id"]: p["delay"] for e in _events(t, "tracking") for p in e.get("parcels", [])}
        for e in _events(t, "tool"):
            if e.get("tool") != "file_carrier_fault":
                continue
            total += 1
            bad += int(track.get(e.get("parcel_id")) != e.get("delay_days"))
    return bad / max(1, total)


MONITORS = {
    "escalation_rate": escalation_rate,     # có sẵn; KHÔNG tính là metric mới của đội
    "model_override_rate": model_override_rate,
    "fault_delay_mismatch_rate": fault_delay_mismatch_rate,
}
STARTER_MONITORS = ("escalation_rate",)
