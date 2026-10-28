# ND2–ND3: Giao thức gán nhãn và kiểm định giá trị bổ sung của biểu diễn hành vi
Ngày chốt bản kế hoạch: 2026-10-28. Trạng thái: đề xuất, **chưa có kết quả ND2/ND3**.

## Câu hỏi nghiên cứu
- **RQ1:** Gán nhãn hành vi có ổn định trên các lượt StudentBench chưa được sử dụng hay không?
- **RQ2:** Nhãn phản ánh hành vi có thể quan sát và có ý nghĩa theo cách hiểu của người đánh giá độc lập không?
- **RQ3:** Nhãn hành vi giúp dự đoán **posttest độc lập sau tutoring** tốt hơn các baseline chỉ gồm pretest, quy mô hội thoại và sự kiện làm bài không?
- **RQ4:** Trình tự các nhãn tạo ra giá trị vượt tần suất các nhãn hay không?

Nguồn: StudentBench official Hugging Face, pinned SHA 304c8d63c726e72b60510bba3a44454fc0726721. Kết quả kiểm định nguồn hiện có: 2.139 session AI tutor, 52.646 student_message, 64.556 sự kiện nộp bài. Có dữ liệu pretest_responses.csv, posttest_responses.csv, student.json và student_practice_problem_attempts.csv. Chú ý: một sự kiện nộp bài không tương đương một bài làm độc lập.

## G0 — Khóa dữ liệu, codebook và nguồn gốc
1. Xác minh lại đầy đủ 40 episode ND1 sang session gốc. Loại khỏi ND2 mọi session trùng hoặc chưa xác minh chắc chắn, không khẳng định holdout nếu còn mơ hồ.
2. Chốt codebook chính thức (primary_act 7 nhãn AK, AN, CQ, HR, OT, RE, VE; feedback_uptake 5 nhãn AC, AP, NO, NR, UN), precedence rules, prompt, phiên bản thực tế của Astra và Claude, cách xử lý ngữ cảnh. Cấm dùng nhãn của annotator A trong lời nhắc của B.
3. Đối chiếu hồ sơ consent, tình trạng pretest/posttest, session trùng và nguồn người học lặp lại. StudentBench có thông tin ẩn danh phục vụ phân tích độ nhạy cho người học lặp lại; không cố tái định danh.
4. Tạo registry session/hash, chia tập trước khi xem nhãn hoặc tối ưu mô hình. Các CSV gốc, mapping và split registry để PRIVATE, đúng .gitignore.

## ND2-A — Gán nhãn độc lập 280 lượt, 280 session
- **200 random:** một lượt student_message được lấy ngẫu nhiên trong mỗi session ngẫu nhiên, sau khi loại ND1; kết quả chính ước lượng accuracy theo session, không phải toàn bộ lượt chat.
- **80 challenge:** 4 nhóm chọn theo tín hiệu từ khóa (coordination, reasoning/verification, help/clarification, reaction), mỗi nhóm 20; dùng session khác random. Chỉ để stress test, **không gộp với 200** để báo cáo headline.
- Mỗi record giữ đúng 8 cột gốc: episode_id, previous_student_excerpt, tutor_context, student_turn, primary_act, feedback_uptake, annotation_rationale, confidence.
- Context bao gồm thông tin **trước** lượt sinh viên, giữ bản đầy đủ để gán chính; không tự cắt 950 ký tự. Không lộ kết quả posttest, tương lai, hay nhãn của mô hình còn lại.
- Astra là **reference quy ước**; Claude annotates độc lập. Log version/model/prompt/hash. Kiểm định đầu vào giống nhau, mã nhãn hợp lệ, không thiếu, ID/order không lệch.
- Chỉ số **chính**: accuracy primary_act của Claude so Astra trên random 200, Wilson 95%. Phụ: macro-F1 trên lớp Astra có support, fixed-all-class sensitivity, uptake accuracy/F1, joint exact, Cohen kappa, confusion/support, confidence/coverage, Quant/Verbal, cấu hình tutor. Báo cáo challenge riêng. Zero-support = chưa có bằng chứng cho lớp đó.
- Phân tích 100% bất đồng và lấy mẫu một số trường hợp đồng thuận để kiểm tra khả năng cùng sai.

## ND2-H — Giá trị nội dung và đánh giá con người
- Mẫu 80–120 lượt để hai người chấm độc lập (tăng nếu chưa có ca hiếm). Nên có cả ca model bất đồng lẫn ca đồng thuận.
- Tách **feedback được biểu hiện trong lời nói** khỏi **hành vi sau phản hồi**. Để chứng minh phản ứng thực tế, phải quan sát timeline tutor/chat/practice có quan hệ thời gian; việc nộp bài không tự động là uptake.
- Đo agreement người-người, adjudication, lỗi hệ thống nhãn. Sửa codebook trên development data rồi đánh giá lại trên test mới, không thay định nghĩa ngay trong heldout set.

## ND2-B — Context ablation (thứ cấp)
- Chọn trước 80–120 ca, so sánh full context với bản cắt 950 chars theo paired design, cùng codebook và model.
- Không thay nhãn tham chiếu giữa hai điều kiện. Báo cáo chênh lệch accuracy, lỗi theo lớp, McNemar paired; điều chỉnh đa kiểm định.
- Không suy diễn mức ảnh hưởng accuracy từ thống kê 51.08% ngữ cảnh dài.

## G1 — Chuyển sang mô hình dự đoán
Chỉ khi codebook và nhãn đạt khả năng diễn giải, có đủ support, và đã gỡ lỗi nghiêm trọng. Accuracy cao trên AC/AP không đủ; cần phân tích NO/NR/UN, lỗi AK/OT và RE/VE. Nếu không đạt: REVISE hoặc RECONSIDER, không tiếp tục giả định ontology đúng.

## ND3-preflight — Khảo sát khả năng dự báo bằng baseline trước khi chi phí gán nhãn lớn
- Tạo bảng outcome (pretest, posttest) và đặc trưng sự kiện đơn giản trên các session hợp lệ, kiểm tra sai lệch và missingness **mà không sử dụng nhãn hành vi**. Không đưa kết quả posttest vào feature input.
- Chốt session split và khóa final test trước mọi phép chọn mô hình. Chạy B0/B1/B2 trên **development train/validation only** để xác nhận baseline có thể tính được và xác định learning curve/khối lượng nhãn hợp lý. Không nhìn metric final test khi điều chỉnh phương pháp.
- Sau khi chốt bộ ND3, tất cả baseline và mô hình có nhãn **phải so sánh trên cùng tập session và cùng folds**; B2 dự đoán trên 2.139 session không được đem so trực tiếp với M3 chỉ có nhãn trên 400–600 session.

## ND3 — Cần **nhiều lượt được gán nhãn trong một session**
- 280 bản ND2 hiện chỉ có **một lượt/session**, không dùng để đánh giá chuỗi. Chọn một mẫu ND3 khác, source-session disjoint ND1/ND2.
- Pilot **40–60 session**, gán toàn bộ student_message theo thứ tự; kiểm tra chi phí và tính nhất quán. Nếu khả thi, mục tiêu 400–600 session, khoảng **9.800–14.800 lượt chat** theo trung bình 24,6 lượt/session. Dùng Astra một nguồn reference để giảm chi phí; Claude và người chấm kiểm tra subset, ghi rõ mức silver label.
- Bài toán chính: dự đoán tổng số câu đúng **posttest 0–27**, với pretest là covariate. Dự đoán sau khi kết thúc tutoring nhưng **trước posttest**. Secondary: gain, và 25% / 50% intervention-cutoff cho early prediction, mỗi lần chỉ dùng thông tin đến mốc đó.
- Tách train/validation/test ở mức session (60/20/20 là đề xuất), có nhóm lặp người học nếu metadata hỗ trợ; giữ test chưa sử dụng trong chọn đặc trưng, codebook, tuning, threshold. Phân tích riêng Quant/Verbal và theo tutor arm.

### Baseline / ablations (giữ thuật toán và split giống nhau)
| ID | Đặc trưng | Câu hỏi |
|---|---|---|
| B0 | Pretest | Đối chứng khả năng ban đầu |
| B1 | Pretest + GRE domain + tutor arm | Điều kiện học và phân công |
| B2 | B1 + số chat, độ dài, thời lượng, số lần thực hành và hiệu suất practice tính trước posttest | **Baseline mạnh và công bằng** |
| M1 | B2 + tần suất/tỷ lệ 7 primary_act | Nhãn hành vi chính có giá trị không? |
| M2 | B2 + tần suất/tỷ lệ feedback_uptake | Uptake có thông tin mới không? |
| M3 | B2 + cả hai nhóm nhãn | **Kiểm định chính: incremental value** |
| M4 | M3 + entropy/chuyển tiếp nhãn kề nhau (chọn ít, định nghĩa trước) | Thứ tự có vượt tần suất không? |

- Mô hình chính: Ridge / ElasticNet, chọn hyperparameter trên validation. Robustness: một mô hình cây cố định trước; không tuyển kết quả đẹp nhất.
- Metric chính: **MAE posttest theo số câu đúng (0–27)**. Thứ cấp RMSE, R² và adjusted gain. Với cùng các session test, định nghĩa **ΔMAE = MAE(B2) − MAE(M3)**; dương ủng hộ giá trị tăng thêm.
- Đánh giá paired bootstrap 95% theo **session** hoặc repeat-person cluster, điều chỉnh cho nhiều ablation; pre-register một so sánh chính **M3 vs B2**. Tham khảo ngưỡng thực tiễn đề xuất 0,25 câu giảm MAE nhưng chốt trước khi mở test.
- Negative controls: hoán vị nhãn giữa session trong strata GRE/tutor (chỉ train), cắt ngữ cảnh, thay nhãn bằng label noise, ablation bỏ uptake hoặc bỏ transitions; đánh giá ổn định qua từng miền.
- Dự đoán tốt hơn là **giá trị dự báo bổ sung**, không chứng minh hành vi là nguyên nhân gây tiến bộ học tập.

## Deliverables và quy tắc quyết định
- ND2: private 280-row Astra/Claude sheets, manifests, disagreement review, human quality audit, context ablation; GitHub chỉ nhận mã và bảng tổng hợp.
- ND3: pre/post join audit, private full-session sequences/labels, split registry; bảng B0/B1/B2/M1–M4, paired ΔMAE 95% CI, class support và error analysis.
- **GO**: ND2 đủ ổn định và có bằng chứng con người xác nhận nội dung hành vi; **REVISE**: thiếu support hoặc lỗi biên có thể khắc phục; **RECONSIDER**: ontology không thể phân biệt bằng bằng chứng quan sát. **ADDED VALUE** chỉ khi M3 đánh bại B2 trên test chưa xem, với hiệu ứng thực tiễn và độ bất định thuyết phục. Kết quả âm cũng phải báo cáo.
- Mọi dữ liệu hội thoại, nhãn theo từng student/session và mapping nguồn **không commit**. Không tuyên bố hiệu năng ND2/ND3 từ kiểm thử giả lập hay audit dữ liệu.
