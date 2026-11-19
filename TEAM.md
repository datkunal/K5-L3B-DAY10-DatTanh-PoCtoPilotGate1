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

## HoVaTen-MSSV

### Phần việc phụ trách

Vai trong bàn; câu nào của đề, mục nào của phiếu A/B/C, file nào (`lab10/guards.py`, `config/operating_gates.json`, …).

### Đóng góp cụ thể

...

### Bằng chứng

Mã commit, mã lần chạy (`runs/<mã>`), dòng trong phiếu.

### Exit ticket

Một điều học được, một điều còn chưa chắc.

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
