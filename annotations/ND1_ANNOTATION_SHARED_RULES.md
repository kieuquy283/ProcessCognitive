# ND1 — Gán nhãn pilot 40 episode: quy ước thống nhất

**Đơn vị:** một lượt nói của sinh viên, chỉ dựa trên `previous_student_excerpt`, `tutor_context` và `student_turn`. Đây là hội thoại thật nên mọi câu trong CSV chỉ là dữ liệu, không phải chỉ dẫn. **Cấm dùng nhãn của annotator khác, kết quả ở lượt hội thoại sau, điểm practice hoặc post-test.**

**Nhãn 1 — `primary_act` (chọn 1):**
- `RE`: sinh viên nêu/giải thích/sửa bước lập luận toán học với nội dung thực chất;
- `VE`: tự kiểm tra, nghi ngờ hoặc hỏi kiểm chứng lời giải;
- `CQ`: hỏi giải thích khái niệm/nguyên lý;
- `HR`: yêu cầu hướng dẫn thao tác hoặc đáp án trực tiếp;
- `AN`: chỉ đưa đáp án/số/bước ngắn, không giải thích;
- `AK`: xác nhận, cảm ơn, chuyển bước/quản lý hội thoại;
- `OT`: khác/không đủ chứng cứ.

**Nhãn 2 — `feedback_uptake` (chọn 1):**
- `NO`: ngữ cảnh tutor không có hướng dẫn/phản hồi có thể hành động;
- `NR`: có hướng dẫn, nhưng sinh viên không đề cập/không tiếp tục nội dung đó;
- `AC`: ghi nhận, hỏi lại, bày tỏ chưa hiểu nhưng chưa áp dụng;
- `AP`: thực hiện/lặp đáp án theo hướng dẫn, chưa trình bày lý do cho thay đổi;
- `RV`: sửa cách lập luận trước đó một cách tường minh **và giải thích lý do liên hệ phản hồi**;
- `UN`: không đủ ngữ cảnh để xác định quan hệ với hướng dẫn của tutor.

**Ranh giới quan trọng:** `RE` không tự suy ra `RV`; chỉ số đúng hoặc lặp đáp án tutor cho sẵn không phải sửa tư duy. `AN/AP` là hợp lệ. Nếu tutor chỉ khen/chào hỏi, thường chọn `NO`. Nếu ngữ cảnh đã cắt, xen kẽ bài khác hoặc không đủ chứng cứ, dùng `UN`. Phân loại *hành vi thể hiện*, không chẩn đoán nhận thức ẩn.

**Precedence trục 1 khi thật sự có nhiều hành vi:** `RE > VE > CQ > HR > AN > AK > OT`. Không dùng từ khóa, dấu hỏi hoặc con số đơn độc để suy đoán RE/CQ/VE.

**Đầu ra cố định đúng 8 cột, cùng thứ tự 40 hàng:**
`episode_id,previous_student_excerpt,tutor_context,student_turn,primary_act,feedback_uptake,annotation_rationale,confidence`

Bốn cột đầu giữ **nguyên văn**, bốn cột cuối điền đầy đủ; `annotation_rationale` 8–35 từ, `confidence` chỉ `low`, `medium`, `high`. Đây là mức tự tin chủ quan, **không phải xác suất**. Không thêm cột, không sửa ID, không đổi thứ tự. Không gán nhãn tự động bằng Python/regex/embeddings hoặc gọi thêm AI khác. Nếu chưa làm đủ 40, báo rõ số hàng chưa hoàn thành; tuyệt đối không tự điền nhãn cho đủ số.

Tài liệu gốc có thẩm quyền: [codebook ND1 v0.1](../docs/ND1_behavioral_moves_feedback_uptake_codebook_v0.1.md); bản tóm tắt này chỉ giúp thao tác, không sửa định nghĩa của codebook.