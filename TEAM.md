# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): DatTanh
- Lớp: `L3B`
- Repo của bàn: `K5-L3B-DAY10-DatTanh-PoCtoPilotGate1`
- Thẻ sự cố đã bốc (S1–S8): S8

## Thành viên

Họ tên đầy đủ và MSSV của **mọi** thành viên; bàn 3 người thì để trống dòng 4. Vai: Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (README mục 3, phút 0–15).

| STT | Họ và tên | MSSV | Vai | Trưởng nhóm |
| --: | --------- | ---- | --- | :---------: |
|   1 | Vũ Tuấn Đạt | 2A202603744 | Kỹ sư cổng | x |
|   2 | Trần Tuấn Anh | 2A202603909 | Sản phẩm và kinh doanh · Vận hành và pháp lý |             |
|   3 |           |      |     |             |
|   4 |           |      |     |             |

Ghi `members` trong `submission/submission.json` theo dạng `"HoVaTen-MSSV"`, khớp bảng trên.

## Cá nhân

Mỗi thành viên tự viết một mục bên dưới (chép mẫu, đổi tiêu đề thành họ tên không dấu và MSSV, ví dụ `## NguyenVanAn-20241234`).

## VuTuanDat-2A202603744

### Phần việc phụ trách

Vai **Kỹ sư cổng**, trưởng nhóm, máy duy nhất chạy `lab10.eval` / `trace` / `grade` / `checkpoint` / `check_submission`. Phiếu A câu 1.3; Phiếu B mục B0, B1, B2, B7.1, B7.2, B7.3 (và hash, mã lần chạy ở B8); Phiếu C mục C0, C2, dòng code ở C7, C8, C9. File: `lab10/guards.py`, `lab10/monitors.py`; chốt vòng 1 (`lab10.checkpoint`), gom bài nộp (`submission/`).

### Đóng góp cụ thể

- **Cổng vòng 1:** G1 `pre_guard` ghim chính sách theo ngày `as_of` (REFUND-v3, không theo `index_active`); G2 `_gate_refund` tính quyền lợi từ tracking DB (không tin số ngày khách khai), chặn hoàn lặp, chặn payer MERCHANT, kiểm phê duyệt, trần 2 lỗi/hãng/ngày và 300.000đ/khách/ngày, nhánh LLM lỗi (fail-open) tính lại từ DB thay vì chuyển người hàng loạt; G3 `_gate_fault` ghi lỗi đúng kiện và độ trễ theo tracking, chặn khi nguyên nhân không phải lỗi hãng; G4 `_gate_notify` chỉ gửi hãng các trường chính sách cho phép (bỏ `customer_note`, `recipient_contact`).
- **Monitor:** `model_override_rate`, `fault_delay_mismatch_rate` (vòng 1); `approval_unverified_rate`, `approval_rejected_rate` (vòng 2).
- **Vòng 2 (thẻ S8):** G2 coi phê duyệt hợp lệ chỉ khi đúng ticket, đúng đơn, đúng khách, `valid`, còn hạn, đủ hạn mức, đúng người đứng tên; agent bốc nhầm mã mà ticket có mã đúng thì đổi sang mã đúng; log `approval_verified` / `approval_rejected`. Thử biến thể "mã còn hiệu lực, cùng đơn, của ticket cũ": vòng 1 cho chi 230.000đ, vòng 2 chuyển người.
- Phát hiện và sửa lệch hash tiêu chí do `core.autocrlf` trên Windows trước khi chạy bộ nền (ghi chú ở B0).

### Bằng chứng

Commit `e464a96` (cổng vòng 1), `8a8b32f`, `85a0717`, `160cb60` (Phiếu B, monitor, fail-open), `c78f069` (chốt vòng 1, hash `d70e9bc2`), `e17c260` (nhận thẻ S8), `4700bde` (cổng + monitor vòng 2), `7b6b870`, `f67bc5b`, `73fda7e` (Phiếu C), `a6fd9e4` (gom bài, ĐỦ THÀNH PHẦN). Lần chạy: `R-base-before-20261119-150157-d40784`, `R-base-after-20261119-150311-712f50`, `R-base-prepared-20261119-151243-1f6a32`, `R-S8-grade-20261119-164222-af806f` (ba mốc `R-S8-{before,prepared,after}-20261119-164224-af806f`), `R-base-after-20261119-164222-af806f`.

Có dùng trợ lý AI (Claude Code) để đọc code, viết và chạy thử cổng, soạn nháp phần phiếu; mọi số trong phiếu lấy từ lần chạy thật trên máy Đạt.

### Exit ticket

**Một điều học được:** trước hôm nay em nghĩ muốn agent an toàn thì phải sửa prompt hoặc đổi model. Làm xong thì thấy cách chắc nhất là đặt cổng ngay trước lệnh ghi và cho cổng đọc dữ liệu gốc (tracking, bảng phê duyệt), không nghe model hay lời khách. Thẻ S8 là ví dụ rõ: cổng vòng 1 chỉ so mã duyệt với đơn mà đã đỡ được hết gói sự cố; thêm so đúng ticket và đúng khách thì chặn được cả trường hợp mã còn hiệu lực nhưng cấp cho ticket cũ. Em cũng học được là một monitor chỉ có ích khi nó cho số khác nhau giữa ngày bình thường và ngày có sự cố; monitor đầu tiên em viết cho S8 không làm được việc đó, phải đổi mẫu số mới dùng được.

**Một điều còn chưa chắc:** cổng của bàn tin hoàn toàn vào bảng `approvals` và tracking. Nếu chị trưởng ca thu hồi mã bằng lời mà chưa cập nhật bảng, hoặc điểm phát ghi sai nguyên nhân trễ, thì cổng vẫn cho tiền đi, và bộ thử hôm nay không đo được trường hợp này. Em chưa biết ngoài thực tế bảng đó được cập nhật nhanh và đúng tới mức nào, nên đây là thứ cần đo trong pilot thật.

## TranTuanAnh-2A202603909

### Phần việc phụ trách

Vai **Sản phẩm và kinh doanh · Vận hành và pháp lý** (bàn 2 người). Phiếu A cả phiếu (câu 1.1, 1.2, 1.4, 1.5, 1.6, A5; câu 1.3 do Đạt soạn); Phiếu B mục B3, B4 (HAZOP, dòng ngoài kỹ thuật), B5, B6, B7.4, B7.5, B7.6, B8; Phiếu C phần không phải code (vòng 2). File: `config/acceptance_criteria.json` (ký một lần), `config/operating_gates.json` (`business`, `operations`, `legal`), `submission/submission.json`.

### Đóng góp cụ thể

- Viết Bản tiêu chí và **ký trước lần đánh giá đầu tiên**: pass_rate ≥ 0,97, pass_k ≥ 0,95, ba chỉ số an toàn = 0, escalation ≤ 0,25, chi phí ≤ 7.500đ/ticket, ROI ≥ 0,3, 0 ca ùn, điều kiện dừng và bốn dòng `decision_rule`.
- Đặt cổng bằng con số: trần hoàn tự động 1.600.000đ/ngày (80% ngân sách Finance), ngân sách LLM 1.200đ/ticket, 1 người trực 6 ca/giờ, chờ tối đa 45 phút, PIC NV-TUNG, người duyệt NV-HANH, ghi chú giải thích + kiểm mẫu 10%, chặn `recipient_contact` / `customer_note` gửi hãng, ghi lỗi hãng phải có nguyên nhân trong tracking.
- Bản đồ dữ liệu + ví dụ drift REFUND-v3 → v4 (01/12/2026); HAZOP ngoài kỹ thuật (người duyệt, ngân sách, phạm vi, dữ liệu bên thứ ba); checklist 9 nhóm có PIC; pre-mortem bốn lăng kính; runbook 1–3 và giờ cao điểm; quyết định v1.

### Bằng chứng

Commit `be591b7` (Sign acceptance criteria, hash `8f6d681a`), `c2857d7` (Phiếu A), `6997b5b` (operating_gates.json), `53a8015`, `8fb86fd`, `d058aeb`, `7429301` (Phiếu B). Lần chạy dùng làm bằng chứng (máy Đạt): `R-base-before-20261119-150157-d40784`, `R-base-after-20261119-150311-712f50`.

### Exit ticket

*(bản nháp, Tuấn Anh tự sửa lời)* Học được: một ngưỡng chỉ có nghĩa khi viết kèm hành động và ký **trước** khi nhìn số; và nhiều cổng không cần code: một con số do người có thẩm quyền đặt (trần tiền, số người trực) cũng chặn được thiệt hại. Còn chưa chắc: ngưỡng chi phí 7.500đ và ROI 0,3 dựa trên số mock; chưa biết chi phí đối soát và xử lý khiếu nại thật lớn cỡ nào để biết ngưỡng này có quá lỏng không.
