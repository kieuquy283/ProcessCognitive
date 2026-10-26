# ND1 — Bắt đầu gán nhãn với Codex Astra & Gemini 4 Argon Web

**Mục tiêu:** Hai AI gán nhãn độc lập **40 episode thật**, theo codebook ND1 v0.1. Chỉ sau bước pilot và phân tích bất đồng mới quyết định mở rộng 180 episode.

**Bước 1 — Một nguồn dữ liệu duy nhất.** Tại checkout nhánh `research/studentbench-diagnostics`, chạy:

```bash
python experiments/nd1_extract_feedback_episodes.py --out annotation_work/new_direction/nd1_pilot_180_PRIVATE.csv --n 180 --per-arm 6
python experiments/nd1_prepare_dual_annotation_40.py --source annotation_work/new_direction/nd1_pilot_180_PRIVATE.csv --out-dir annotation_work/new_direction
```

Bộ 180 episode được tạo từ StudentBench GRE Quant, phiên bản dữ liệu đã cố định, 78 phiên thuộc 13 tutor arms. Bộ 40 cho hai AI phải **cùng ID và thứ tự**, bốn ô nhãn cuối trống. Script kiểm tra tự tạo SHA-256 chung.

**Bước 2 — Hai cuộc hội thoại mới, mù nhãn lẫn nhau.**

- **A (Codex Astra):** dùng [prompt A](ND1_CODEX_ASTRA_A_40_TASK.md); nguồn `ND1_pilot_40_blind.csv); xuất `ND1_Astra_A_40.csv`. Codex phải thực sự tạo file trên máy, không chỉ báo “đã xong”.
- **B (Gemini 4 Argon Web):** chỉ gửi `ND1_Gemini4Argon_B_40_UPLOAD.csv` và dán [prompt B](ND1_GEMINI_4_ARGON_WEB_B_40_PROMPT.md); yêu cầu trả `ND1_Gemini4Argon_B_40.csv`. Nếu model khác tên, ghi lại chính xác tên được chọn trong UI.

Cả hai tuân theo [codebook ND1 gốc](../docs/ND1_behavioral_moves_feedback_uptake_codebook_v0.1.md). **Không gửi** file annotator kia, bảng tổng hợp, điểm post-test hay nội dung tương lai. Trước khi tải lên Gemini, kiểm tra riêng các đoạn hội thoại có thể tiết lộ danh tính; sàng lọc PII tự động không bảo đảm an toàn tuyệt đối.

**Bước 3 — Thu hai CSV và kiểm chứng sau khi cả hai hoàn thành.**

```bash
python experiments/nd1_validate_annotations.py --source annotation_work/new_direction/ND1_pilot_40_blind.csv --file annotation_work/new_direction/ND1_Astra_A_40.csv --n 40
python experiments/nd1_validate_annotations.py --source annotation_work/new_direction/ND1_pilot_40_blind.csv --file annotation_work/new_direction/ND1_Gemini4Argon_B_40.csv --n 40

python experiments/nd1_agreement.py \
 --source annotation_work/new_direction/ND1_pilot_40_blind.csv \
 --a annotation_work/new_direction/ND1_Astra_A_40.csv \
 --b annotation_work/new_direction/ND1_Gemini4Argon_B_40.csv \
 --n 40 --out annotation_work/new_direction/ND1_40_agreement.json
```

Báo cáo riêng **hai trục** primary act và feedback uptake: agreement, Cohen κ, ma trận nhầm lẫn và case bất đồng. Đặc biệt xem `AN/AP`, `RE/RV`, `AC/AP/RV`, `NO/UN`. **Đồng thuận AI–AI không phải xác thực bởi con người.**

**Quyết định sau pilot:** Nếu nhiều nhãn bất đồng, sửa codebook lên v0.2 và thực hiện pilot mới. Nếu ổn, mới tăng lên 180 case; luôn dành mẫu review của người có chuyên môn. **Không dùng script tự điền nhãn, không công bố hội thoại hoặc nhãn private lên repo công khai.**
