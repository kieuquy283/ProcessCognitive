# Báo cáo tổng kết E7–E14 và tái thiết kế hướng nghiên cứu ProcessCognitive

**Ngày:** 25/10/2026  
**Trạng thái:** Kết thúc nhánh thực nghiệm dự đoán post-test; khởi động ND1 — *Student Behavioral Moves and Feedback Uptake*.  
**Dữ liệu chính:** StudentBench, GRE Quantitative, phiên bản đóng băng `304c8d63c726e72b60510bba3a44454fc0726721`.  
**Mức độ xác nhận:** Các kết quả E7–E14 là thực nghiệm khám phá/nội bộ trên StudentBench, chưa phải bằng chứng khái quát trên quần thể giáo dục khác.

## 1. Tóm tắt điều hành

Chuỗi E7–E14 đánh giá giả thuyết rằng dấu vết hội thoại, ánh xạ ngữ nghĩa concept–skill và lịch sử hành động theo thời gian của sinh viên có thể cải thiện dự báo **đúng/sai ở independent GRE post-test**, sau khi kiểm soát năng lực pre-test, đáp án pre-test cùng nhóm câu hỏi và tình hình làm practice. Các hướng TF-IDF/embedding, GRU, concept–skill alignment dùng nhãn silver GPT-6 Astra, và practice-process features **đều chưa chứng minh được lợi ích dự báo bổ sung ổn định**. Mô hình P_attempts có lợi thế điểm ước lượng trên development E13 nhưng không lặp lại được trên 125 phiên holdout nội bộ E14 (Log Loss baseline 0,538238; P_attempts 0,540086; chênh lệch lợi ích −0,001848, bootstrap 95% [−0,006090; +0,001470]).

Do đó **dừng phát triển kiến trúc/hyperparameter với cùng giả thuyết mục tiêu**. Tuy nhiên không thể suy ra rằng hội thoại học tập không có thông tin hoặc người học không tiến bộ nhờ AI. Giả thuyết âm chỉ có hiệu lực với những **biểu diễn, biến kiểm soát, dữ liệu và giao thức đã thử**.

Chuyển hướng đề xuất: **mô hình hóa hành vi diễn ngôn có thể quan sát được khi sinh viên tiếp nhận phản hồi của AI**, đo trực tiếp ở cấp *student-turn episode*. Giá trị của hướng mới phải được xác nhận trước hết bằng chất lượng định nghĩa hành vi, mức độ thống nhất của người gán nhãn và khả năng tổng quát hóa, **không** bắt buộc vượt baseline dự đoán post-test.

## 2. Kết quả thực nghiệm và quyết định

| Nhóm | Cách tiếp cận | Kết luận theo dữ liệu đã thử |
|---|---|---|
| **E7–E8** | TF-IDF, embedding ngữ nghĩa, biểu diễn sự kiện và sequence/GRU | Không có cải thiện được tái lập một cách vững chắc so với baseline kiểm soát pre-test/practice. |
| **E9–E10** | Semantic/concept-conditioned matching và ánh xạ 120 nhãn GPT-6 Astra | Có thể học một phần ranh giới S/N của Astra, nhưng không thấy giá trị dự báo post-test bổ sung. Nhãn D trực tiếp ban đầu cực ít (5/120). |
| **E11** | Bổ sung 400 cặp concept–subskill; hai mô hình Astra/Gemini gán nhãn | Đồng thuận mô hình trên 400 cặp 88,75%, κ≈0,826; nhưng phân bố D bị chi phối mạnh bởi mẫu tăng cường. Đồng thuận AI–AI **không phải human ground truth**. |
| **E12** | Huấn luyện ánh xạ từ 400/520 nhãn silver và kiểm thử trên StudentBench | Bộ nhãn nhiều hơn không giúp vượt baseline (ví dụ C=0,03, 456 phiên development: Log Loss B0 0,526484 so với Astra-400 0,527854). |
| **E13** | Đúng/sai lần thử đầu, sửa đáp án, trật tự tương tác và 20 hoán đổi | B1 có điểm ước lượng tốt hơn nhưng CI bao gồm 0; B2 đầy đủ chuỗi kém hơn B1. Ablation số lần thử là *post-hoc*. |
| **E14** | Cố định P_attempts từ E13, đánh giá duy nhất trên holdout nội bộ | **Không tái lập cải thiện**: B0 0,538238, P_attempts 0,540086; 18/20 mô hình hoán đổi đặc trưng huấn luyện có điểm Log Loss thấp hơn mô hình dùng đặc trưng thật. |

**Phân biệt thiết yếu:** “Không chứng minh được lợi ích” khác với “đã chứng minh mọi phương pháp hội thoại đều vô ích”. Hơn nữa, các nhãn Astra ở E9–E12 được coi là **silver reference theo giả định thực nghiệm**, không phải bằng chứng chuyên gia về hiểu biết toán học.

## 3. Chẩn đoán nguyên nhân và giới hạn suy luận

**3.1. Lệch construct và outcome.** Những gì muốn quan sát — sinh viên giải thích, đánh giá lập luận, nhận phản hồi và tự điều chỉnh — được thay thế bằng proxy (title, embedding, số lượt nhắn). Đánh giá hoàn toàn qua post-test khiến construct gần bị bỏ qua.

**3.2. Baseline giàu thông tin.** Pre-test kết hợp bài practice đã phản ánh nhiều biến liên quan kết quả cuối. Cần chứng minh *incremental predictive validity*, không chỉ tương quan với post-test. E13/E14 chỉ ra nguy cơ chọn mô hình dựa trên nhiễu ở development.

**3.3. Thiếu nhãn định nghĩa trực tiếp.** E9–E12 dùng bộ nhãn Astra về tên concept, không phải phát ngôn sinh viên hay bằng chứng tiếp nhận phản hồi. Dù agreement cao, mức độ đúng về mặt giáo dục chưa được thẩm định độc lập.

**3.4. Giới hạn dữ liệu và đánh giá.** Một số experiment tải mẫu phụ khác nhau; tập được giữ riêng E14 thuộc cùng hệ thống StudentBench đã bị thăm dò ở nhiều vòng; các bootstrap CI phụ thuộc mô hình đã chọn và không điều chỉnh tất cả multiple comparisons. Kết quả không phải xác nhận ngoài miền hay ước lượng nhân quả.

## 4. Đề xuất hướng mới: Observable Feedback Uptake in Human–AI Tutoring

**Tên làm việc (có thể sửa sau pilot):** *Modeling Student Behavioral Moves and Feedback Uptake in Human–AI Tutoring Dialogues*.

**Đơn vị phân tích:** một `student_message`, đặt trong ngữ cảnh một tutor message ngay trước đó, và nếu cùng bài practice thì thêm lượt sinh viên trước để phân biệt việc sửa lập luận. **Không** hiển thị đáp án practice xảy ra sau student turn hoặc điểm post-test khi gán nhãn.

**RQ1 — Measurement validity:** Có định nghĩa và gán nhãn được các hành vi diễn ngôn và cách sinh viên đáp lại phản hồi một cách đủ rõ, có thể lặp lại giữa các người đánh giá?

**RQ2 — Modeling:** Ngữ cảnh phản hồi của tutor có cải thiện khả năng nhận diện *feedback uptake* so với chỉ đọc lời sinh viên không? So sánh cùng chia dữ liệu và ngân sách, có đối chứng hoán đổi ngữ cảnh.

**RQ3 — External behavioral validity:** Những hành vi đã được gán nhãn đáng tin cậy có liên hệ với hành động practice tiếp theo (ví dụ sửa từ sai sang đúng) sau khi kiểm soát mức đúng trước đó và kiểu bài? Đây là liên hệ quan sát, **không phải** bằng chứng nhân quả hay “learning gain” dài hạn.

**RQ4 — Transfer (mở rộng khi có bằng chứng):** Nhãn có tổng quát hóa sang tutor arm, task/concept và một dataset độc lập (ví dụ StudyChat, sau khi đối chiếu ontology) hay không? Nếu không cùng định nghĩa thì **không** gộp trực tiếp.

### 4.1. Công cụ đo lường hai trục (ND1 codebook v0.1)

*Hành vi chính* `primary_act`: **RE** trình bày lập luận, **VE** kiểm tra/giám sát, **CQ** hỏi khái niệm, **HR** yêu cầu giúp đỡ/giải đáp, **AN** đáp án ngắn không giải thích, **AK** xác nhận/quản lý hội thoại, **OT** khác/không đủ chứng cứ.

*Phản hồi được tiếp nhận* `feedback_uptake`: **NO** không có phản hồi/hướng dẫn hành động, **NR** không liên hệ nội dung phản hồi, **AC** ghi nhận/hỏi lại nhưng chưa áp dụng, **AP** áp dụng hoặc lặp câu trả lời chưa lý giải, **RV** chủ động sửa lập luận với lý do được diễn đạt, **UN** không đủ bối cảnh để quyết định.

**Không suy diễn trạng thái tâm lý từ lời nói.** Đặc biệt, lặp đáp án tutor cho sẵn được xếp AP, không tự động là RV; một câu trả lời sai vẫn có thể là RE. Nguồn đầy đủ và precedence: [codebook ND1](../docs/ND1_behavioral_moves_feedback_uptake_codebook_v0.1.md).

### 4.2. Positioning với literature (chưa tuyên bố novelty)

- **StudentBench** cung cấp dialogue, practice và pre/post GRE trên người học thực; nghiên cứu gốc tập trung nhiều vào *learning gains* và khác biệt tutor. Dữ liệu phù hợp làm nguồn episode nhưng không cung cấp sẵn “feedback uptake” chuẩn như ontology ND1.
- **StudyChat** chứng minh có thể nghiên cứu dialogue act của sinh viên và liên hệ outcomes trong môi trường tương tác với LLM. ND1 cần chỉ rõ khác biệt giữa một lượt yêu cầu và **chứng cứ áp dụng phản hồi**.
- **MathDial** nghiên cứu strategy của tutor và grounded reasoning; nhắc rằng không thể đồng nhất chiến lược tutor với mức hiểu của sinh viên.
- **TutorBench** đánh giá feedback/hint/adaptation; có giao thoa với ND1 nên novelty phải được kiểm tra nghiêm túc trước khi đặt tên phương pháp mới.

**Research gap chỉ là giả thuyết có điều kiện:** liệu biểu diễn *student feedback uptake* dựa trên episode có vừa định nghĩa được đáng tin cậy vừa mang giá trị dự đoán hành động tiếp theo ở GRE hay không. Cần khảo sát hệ thống bổ sung để khẳng định tính mới.

## 5. Đã khởi động bằng dữ liệu thật — ND1 episode pilot

Script `experiments/nd1_extract_feedback_episodes.py` đã chạy trên release StudentBench đã cố định:

| Chỉ tiêu | Giá trị quan sát |
|---|---:|
| Tutor arms | 13 |
| Session lấy mẫu và tải đủ | **78/78** |
| Lượt sinh viên có ngữ cảnh đủ điều kiện | **1.795** |
| Episode chọn cho pilot mù | **180** |
| Phiên khác nhau trong pilot | **68** |
| Episode tối đa / phiên | **4** |
| Sampling panels | 54 reasoning-heuristic, 45 feedback-followup-heuristic, 45 short-response-heuristic, 36 unrestricted-other |
| Ngữ cảnh tutor và lượt sinh viên có cùng practice ID rõ ràng | **99,4%** |
| Episode có một đoạn văn bản dài bị cắt ngắn | **37** |
| **Nhãn từ con người** | **0 — chưa bắt đầu** |

Đây là **mẫu chủ đích** để kiểm tra định nghĩa codebook, không phải lấy mẫu ngẫu nhiên đại diện. Các nhãn `reasoning_candidate` v.v. chỉ là **điều kiện chọn mẫu bằng từ khóa/độ dài**, tuyệt đối không phải nhãn hành vi có giá trị làm ground truth. Không có dự báo post-test nào được chạy trong hướng ND1.

**Lưu ý:** Bộ 180 episode chứa phát ngôn người thật, được lưu ở đầu ra *private local* của script, không commit lên GitHub. Trước khi chuyển cho hai người gán nhãn cần rà soát PII, ngữ cảnh có bị cắt, và sự xen kẽ hai bài practice trong cùng phiên. Bản code sau cùng hạn chế `previous_student_excerpt` về cùng `practice_problem_id`; cần tái tạo private pilot theo commit mới khi sử dụng để annotate.

## 6. Giao thức triển khai, điều kiện dừng và chống leakage

**P0 — Feasibility pilot:** Hai người hiểu nền tảng GRE Quant được yêu cầu independently double-annotate trước **40 episode thật**, giữ mù kết quả của nhau, đánh giá cả hai trục. Nếu chỉ dùng Astra/Gemini thì báo cáo **model–model reliability**, không gọi human κ. Phân tích disagreement và cập nhật codebook v0.2, lưu nguyên v0.1. Không thử classifier trong khi nhãn chưa được thẩm định.

**P1 — Main annotation:** Annotate phần còn lại của 180 episode theo codebook đóng băng; ít nhất 60 case được gán đôi bởi người thật nếu khả thi. Theo dõi κ và confusion từng nhãn; `RV` hiếm phải báo precision/positive agreement thay vì chỉ nhìn overall accuracy. Không ép các nhãn cân bằng.

**P2 — Baselines:** Session-grouped split, majority/stratified prior, student-only TF-IDF LR, preceding-tutor+student TF-IDF LR; thêm embedding/LLM khi cùng fold/cùng ngân sách. Kiểm tra lợi ích của tutor context bằng shuffle/mismatched context negative control. Kết quả trên một pilot 180 nhỏ **chỉ có giá trị feasibility**, không đủ để tuyên bố SOTA hoặc tổng quát hóa.

**P3 — Outcome independence:** Chỉ dùng các lượt practice tiếp theo để đánh giá liên hệ hành vi nếu anchor là trước kết quả cần dự đoán; đo độ đúng/sai trước đó, lần nộp kế tiếp, tutor arm và nguồn bài tập. Không sử dụng dữ liệu tương lai để gán nhãn hoặc làm feature. Điểm post-test chỉ là kiểm tra giá trị bên ngoài mang tính thăm dò.

**Decision gate:**
- Nếu người gán nhãn thường xuyên không phân biệt được `AC/AP/RV` hoặc nhiều trường hợp `UN`, **sửa construct/codebook**, không huấn luyện tiếp để tìm metric tốt.
- Nếu mô hình ngữ cảnh không hơn student-only hoặc không hơn context-shuffle sau khi nhãn đáng tin, báo cáo giới hạn của quan hệ feedback; không tạo “mô hình nhận thức” mới dựa trên kết quả âm.
- Chỉ khẳng định đóng góp phương pháp khi có chất lượng nhãn độc lập, đối chứng chặt và kiểm định task/session-disjoint phù hợp.

## 7. Lộ trình ngắn hạn

| Giai đoạn | Kết quả bàn giao |
|---|---|
| Tuần 1 | Đối chiếu literature, kiểm toán 180 episode/PII, 40 case gán nhãn mù 2 người, báo cáo confusions |
| Tuần 2 | Chốt codebook v0.2, mở rộng nhãn, thiết kế phép đo reliability và split theo session |
| Tuần 3–4 | Huấn luyện baseline student-only vs tutor-context; context shuffle; kiểm tra calibration, rare labels |
| Tuần 5–6 | Gắn practice outcome sau episode với timeline chính xác, phản biện observational/causal, quyết định mở rộng data |
| Sau đó | Replication ở tutor arm khác hoặc dataset khác, viết chương phương pháp và đánh giá |

Không đưa ra timeline như một lời hứa thực hiện tự động; đây là kế hoạch nghiên cứu có mốc quyết định.

## 8. Giới hạn hiện tại

Hướng ND1 **chưa được chứng minh hiệu quả**. Mẫu 180 còn nhỏ, lấy có chủ đích, có 37 đoạn bị cắt, việc “uptake” đòi hỏi xác định **tutor feedback có actionable hay không**, transcript có thể ghi sai/không đầy đủ và một lượt người học không phản ánh trạng thái nhận thức thật. Việc kiểm soát PII và hành vi data leakage phải được thực hiện trước mọi đánh giá người thật hay mô hình. Các khả năng học được nhãn từ 180 mẫu và chuyển giao sang StudyChat/FLoRA hiện chỉ là giả thuyết.

**Kết luận:** Đã quyết định dừng nhánh E7–E14 với kết quả âm được bảo toàn. ND1 đã có codebook sơ bộ và 180 episode thật để bắt đầu kiểm chứng **khả năng đo lường**, nhưng **chưa có nhãn gold, chưa có reliability, chưa có model score**. Không nên biến giai đoạn khởi động thành tuyên bố thành công.

## Tài liệu tham khảo

1. Northcutt C. và cộng sự (2026). *StudentBench: AI and human tutoring yield equivalent GRE learning gains*. https://arxiv.org/abs/2609.28470
2. McNichols H. và cộng sự (2026). *The StudyChat Dataset: Analyzing Student Dialogues With ChatGPT in an Artificial Intelligence Course*. https://arxiv.org/abs/2503.07928
3. Macina J. và cộng sự (2023). *MathDial: A Dialogue Tutoring Dataset with Rich Pedagogical Properties Grounded in Math Reasoning Problems*. Findings of EMNLP. https://aclanthology.org/2023.findings-emnlp.372/
4. Srinivasa R. S. và cộng sự (2025). *TutorBench: A Benchmark To Assess Tutoring Capabilities Of Large Language Models*. https://arxiv.org/abs/2510.02663
5. E7–E14 experiment reports, [ProcessCognitive](https://github.com/kieuquy283/ProcessCognitive/tree/research/studentbench-diagnostics/reports).
