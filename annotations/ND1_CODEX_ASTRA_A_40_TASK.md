# ND1 Pilot — Hướng dẫn Codex Astra (Annotator A)

**Nhiệm vụ:** Gán nhãn **40 lượt hội thoại sinh viên thật** trong cùng bộ pilot ND1; tạo một file CSV duy nhất để so sánh mù với Annotator B (Gemini 4 Argon Web). Nhãn là **silver**, không phải human ground truth.

**Nguồn dùng duy nhất:** bộ CSV 40 dòng `ND1_pilot_40_blind.csv` do người nghiên cứu đặt trong `annotation_work/new_direction/`; không lấy từ bản 180 khác nếu ID/hàng không khớp. Đọc codebook chung `docs/ND1_behavioral_moves_feedback_uptake_codebook_v0.1.md` và [quy ước v0.1](ND1_ANNOTATION_SHARED_RULES.md). Không xem kết quả annotator B, tài liệu E7–E14, kết quả correctness/tương lai. Nên bắt đầu phiên Codex mới, chọn đúng cấu hình **GPT-6 Astra** và kiểm tra model thực tế đang dùng.

**Giao việc:**

1. Đọc nguồn và kiểm tra chính xác **40 ID khác nhau**, 4 cột đầu nguyên vẹn, 4 cột nhãn đều trống. Không chỉnh sửa nguồn.
2. Tự đọc từng episode, chọn `primary_act` (RE/VE/CQ/HR/AN/AK/OT), sau đó chọn `feedback_uptake` (NO/NR/AC/AP/RV/UN). Đặc biệt xem kỹ quy tắc `RE≠RV`, `AN/AP`, và trường hợp `NO` so với `UN`.
3. Viết 8–35 từ `annotation_rationale`, nêu bằng chứng từ đoạn hiển thị; đặt `confidence` là `low`/`medium`/`high`.
4. Xuất **`annotation_work/new_direction/ND1_Astra_A_40.csv`** với **đúng 40 hàng và 8 cột ban đầu**, giữ nguyên thứ tự và chữ trong 4 cột nguồn, UTF-8. Không ghi nhãn mẫu vào repo công khai.
5. Chạy bộ kiểm tra cục bộ:
   ```bash
   python experiments/nd1_validate_annotations.py \
     --source annotation_work/new_direction/ND1_pilot_40_blind.csv \
     --file annotation_work/new_direction/ND1_Astra_A_40.csv --n 40
   ```
6. Chỉ báo cáo: model thực tế, số hàng hoàn thành, đường dẫn CSV và tình trạng validator. **Không tính agreement và không truy cập output của Gemini.**

**Không sử dụng script để quyết định nhãn**. Có thể dùng code để đọc/ghi/kiểm tra cấu trúc CSV; nội dung phân loại phải do Astra đánh giá từng trường hợp. Hãy xuất file thật, không chỉ mô tả rằng đã hoàn thành.

**Bảo mật:** CSV chứa hội thoại sinh viên thật, chỉ lưu cục bộ trong `annotation_work/`; không commit hoặc công bố.