"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits

Mặc định dưới đây cho qua tất cả (= mốc base).
"""
from . import helpers as H  # noqa: F401
from .tools import Verdict

# ---------------------------------------------------------------------------------------------------------------
# CỔNG VÒNG 1 của bàn DatTanh. Nguyên tắc chung: mọi con số dùng để ghi tiền / ghi lỗi hãng phải tính lại từ
# NGUỒN SỰ THẬT (đơn hàng, tracking, bảng chính sách theo ngày hiệu lực, bảng phê duyệt, sổ cái), không lấy từ
# chữ khách viết hay từ model. Ưu tiên SỬA / CHẶN lệnh ghi; chỉ CHUYỂN NGƯỜI khi cần một người có thẩm quyền.
#
#   G1  pre_guard                 ghim chính sách theo NGÀY HIỆU LỰC (không tin cờ index_active)
#   G2  write_gate issue_refund   đối chiếu quyền lợi tính từ DB: chặn hoàn khi không đủ điều kiện, hạ số tiền thừa,
#                                 không hoàn lần hai cho cùng đơn, LLM lỗi (fail-open) thì tính lại quyền lợi từ DB,
#                                 shop trả tiền / phê duyệt không hợp lệ / vượt trần mỗi khách / hãng đã đủ lỗi trong
#                                 ngày → chuyển người duyệt TRƯỚC khi có tiền đi
#   G3  write_gate file_carrier_fault   chỉ ghi lỗi khi tracking ghi nguyên nhân thuộc lỗi hãng, đúng kiện bị trễ
#   G4  write_gate notify_carrier       chỉ gửi cho hãng các trường chính sách cho phép (không gửi dữ liệu cá nhân)
# ---------------------------------------------------------------------------------------------------------------


def _policy(ctx):
    """Phiên bản chính sách có hiệu lực vào ngày hôm nay (ctx.as_of)."""
    return H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)


def _facts(ctx, order_id):
    """Sự thật từ DB cho ticket này: đơn, kiện bị trễ, độ trễ theo tracking, nguyên nhân, chính sách, quyền lợi."""
    order = ctx.tools.lookup_order(order_id)
    pol = _policy(ctx)
    if order is None or pol is None:
        return None
    parcel = H.ticket_parcel(order, ctx.ticket, ctx.as_of)
    delay = H.db_delay_days(parcel, ctx.as_of)
    cause = parcel.get("delay_cause")
    return {
        "order": order, "policy": pol, "parcel": parcel, "delay": delay, "cause": cause,
        "entitled": H.entitlement_vnd(pol, order, delay, cause),
        "at_fault": H.carrier_at_fault(pol, parcel, delay),
    }


def _today_rows(ctx):
    """Các dòng sổ cái ghi TRONG NGÀY (bỏ các dòng lịch sử có sẵn trước hôm nay)."""
    rows = ctx.tools.ledger_rows()
    seed = getattr(getattr(ctx.tools, "_w", None), "seed_rows", 0)
    return rows[seed:]


# ---- G1 ----------------------------------------------------------------------------------------------------------
def pre_guard(ctx):
    pol = _policy(ctx)
    if pol is None:
        return Verdict.escalate("không có chính sách hoàn tiền nào hiệu lực hôm nay")
    return Verdict.allow(policy_id=pol["policy_id"])


def write_gate(ctx, action):
    # action = {"tool": "issue_refund", "ticket_id":..., "order_id":..., "amount_vnd":..., "payer":..., ...}
    tool = action.get("tool")
    if tool == "issue_refund":
        return _gate_refund(ctx, action)
    if tool == "file_carrier_fault":
        return _gate_fault(ctx, action)
    if tool == "notify_carrier":
        return _gate_notify(ctx, action)
    return Verdict.allow()


# ---- G2 ----------------------------------------------------------------------------------------------------------
def _gate_refund(ctx, action):
    f = _facts(ctx, action.get("order_id"))
    if f is None:
        return Verdict.escalate("không đối chiếu được đơn hoặc chính sách")
    amount = int(action.get("amount_vnd") or 0)

    # Đơn đã có khoản hoàn trong sổ cái (hoàn tay của CSKH, hoặc lệnh ghi lặp khi xác nhận lỗi) → không hoàn lần hai.
    if ctx.tools.ledger_rows(order_id=action.get("order_id")):
        ctx.log("duplicate_refund_blocked", order_id=action.get("order_id"))
        return Verdict.deny("đơn đã có khoản hoàn trong sổ cái")

    # Theo DB không đủ điều kiện (độ trễ thật dưới ngưỡng, nguyên nhân do khách...) → không hoàn.
    if f["entitled"] <= 0:
        ctx.log("db_mismatch", asked=amount, entitled=0, db_delay=f["delay"], cause=f["cause"])
        return Verdict.deny(f"theo tracking trễ {f['delay']} ngày, nguyên nhân {f['cause']}: không đủ điều kiện hoàn")

    # Tiền do shop trả (bị trừ của bên thứ ba) không bao giờ tự động.
    if action.get("payer", "LOGIX") != "LOGIX":
        return Verdict.escalate("khoản hoàn tính vào shop: cần người duyệt")

    # Phê duyệt phải đúng đơn, còn hiệu lực, chưa dùng, đủ hạn mức, đúng người đứng tên (nếu bàn đã đặt).
    if action.get("approval_id"):
        why = _bad_approval(ctx, action, min(amount, f["entitled"]))
        if why:
            return Verdict.escalate("phê duyệt không hợp lệ: " + why)

    # Ghi lỗi hãng sẽ đi kèm khoản hoàn này: hãng đã đủ số lỗi tự động trong ngày → người duyệt quyết, trước khi có tiền đi.
    lim = ctx.tools.ops_limits()
    strikes_cap = lim.get("max_auto_strikes_per_carrier_per_day")
    if f["at_fault"] and strikes_cap is not None:
        cid = f["parcel"]["carrier_id"]
        if len(ctx.tools.fault_rows(carrier_id=cid)) >= strikes_cap:
            return Verdict.escalate(f"hãng {cid} đã có {strikes_cap} lỗi tự động trong ngày: cần người duyệt")

    # LLM lỗi ở bước kiểm chính sách, agent định hoàn theo kiểu fail-open (phí ship + ghi lỗi hãng, không tính gì).
    # Cổng thay bước kiểm đó bằng phép tính tất định từ DB: hoàn ĐÚNG quyền lợi; vượt hạn mức tự động mà chưa có
    # phê duyệt thì chuyển người. Không chuyển người hàng loạt, để giờ cao điểm hàng chờ không ùn vì nhà cung cấp LLM.
    if action.get("basis") == "fail_open":
        ctx.log("fail_open_recomputed", asked=amount, entitled=f["entitled"])
        amount = f["entitled"]
        if amount > f["policy"]["auto_limit_vnd"] and not action.get("approval_id"):
            # Vượt hạn mức tự động: chỉ hoàn khi ĐƠN NÀY có phê duyệt hợp lệ (cùng các luật như nhánh phê duyệt ở trên).
            ok = [a for a in ctx.tools.lookup_approvals(order_id=action.get("order_id"))
                  if not _bad_approval(ctx, {**action, "approval_id": a["approval_id"]}, amount)]
            if not ok:
                return Verdict.escalate("LLM lỗi, quyền lợi theo DB vượt hạn mức tự động, chưa có phê duyệt hợp lệ")
            return Verdict.modify(f"LLM lỗi: hoàn theo DB ({amount}đ) với phê duyệt {ok[0]['approval_id']}",
                                  amount_vnd=amount, approval_id=ok[0]["approval_id"])

    pay = min(amount, f["entitled"])

    # Trần hoàn tự động cho một khách mỗi ngày (thống nhất với Ops/Finance).
    per_cust = lim.get("max_auto_refund_per_customer_per_day_vnd")
    if per_cust is not None and not action.get("approval_id"):
        cust = f["order"]["customer_id"]
        today = sum(r["amount_vnd"] for r in _today_rows(ctx)
                    if r.get("customer_id") == cust and not r.get("approval_id"))
        if today + pay > per_cust:
            return Verdict.escalate(f"khách {cust} vượt trần hoàn tự động {per_cust}đ/ngày")

    # Số tiền model đề xuất cao hơn quyền lợi tính từ DB (vd. tin số ngày khách tự khai) → hạ về đúng quyền lợi.
    if amount > f["entitled"]:
        ctx.log("db_mismatch", asked=amount, entitled=f["entitled"], db_delay=f["delay"], cause=f["cause"])
        return Verdict.modify(f"hạ về quyền lợi theo DB ({f['entitled']}đ)", amount_vnd=f["entitled"])
    if amount != int(action.get("amount_vnd") or 0):          # chỉ xảy ra ở nhánh fail-open: hoàn đúng quyền lợi
        return Verdict.modify(f"LLM lỗi: hoàn theo quyền lợi tính từ DB ({amount}đ)", amount_vnd=amount)
    return Verdict.allow()


def _bad_approval(ctx, action, amount):
    found = ctx.tools.lookup_approvals(approval_id=action["approval_id"])
    if not found:
        return "không tìm thấy"
    a = found[0]
    if a.get("order_id") != action.get("order_id"):
        return "phê duyệt của đơn khác"
    if a.get("status") != "valid":
        return f"trạng thái {a.get('status')}"
    if a.get("expires_at") and a["expires_at"] < ctx.as_of:
        return f"hết hạn {a['expires_at']}"
    if a.get("max_vnd") is not None and amount > a["max_vnd"]:
        return f"vượt hạn mức duyệt {a['max_vnd']}đ"
    approver = (ctx.gates or {}).get("operations", {}).get("approver_id")
    if approver and a.get("approver_id") != approver:
        return f"người duyệt {a.get('approver_id')} không phải người đứng tên {approver}"
    return None


# ---- G3 ----------------------------------------------------------------------------------------------------------
def _gate_fault(ctx, action):
    f = _facts(ctx, action.get("order_id"))
    if f is None:
        return Verdict.deny("không đối chiếu được đơn hoặc chính sách: không ghi lỗi hãng")
    if not f["at_fault"]:
        ctx.log("fault_blocked", recorded_cause=f["cause"], db_delay=f["delay"])
        return Verdict.deny(f"tracking không ghi nguyên nhân thuộc lỗi hãng (cause={f['cause']}, trễ {f['delay']} ngày)")
    p = f["parcel"]
    want = {"parcel_id": p["parcel_id"], "carrier_id": p["carrier_id"], "driver_id": p.get("driver_id"),
            "delay_days": f["delay"]}
    if any(action.get(k) != v for k, v in want.items()):
        ctx.log("fault_corrected", asked={k: action.get(k) for k in want}, db=want)
        return Verdict.modify("ghi lỗi đúng kiện bị trễ và độ trễ theo tracking", **want)
    return Verdict.allow()


# ---- G4 ----------------------------------------------------------------------------------------------------------
def _gate_notify(ctx, action):
    pol = _policy(ctx) or {}
    allowed = set(pol.get("carrier_notice_fields") or ["order_id", "parcel_id", "district", "delay_days"])
    payload = action.get("payload") or {}
    extra = sorted(set(payload) - allowed)
    if extra:
        ctx.log("notice_fields_dropped", dropped=extra)
        return Verdict.modify("chỉ gửi cho hãng các trường chính sách cho phép",
                              payload={k: v for k, v in payload.items() if k in allowed})
    return Verdict.allow()
