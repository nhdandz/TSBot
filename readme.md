BÁO CÁO NGHIÊN CỨU CHI TIẾT: ĐÁNH GIÁ KIẾN TRÚC VÀ LỘ TRÌNH PHÁT TRIỂN HỆ THỐNG CHATBOT AI TƯ VẤN TUYỂN SINH QUÂN SỰ VIỆT NAM (PHIÊN BẢN NÂNG CAO)
1. TỔNG QUAN ĐIỀU HÀNH VÀ PHẠM VI NGHIÊN CỨU
Hệ thống giáo dục và tuyển sinh quân sự tại Việt Nam đặc trưng bởi tính chất pháp lý chặt chẽ, quy định phức tạp và sự phụ thuộc cao vào các dữ liệu lịch sử (điểm chuẩn, chỉ tiêu). Tài liệu thiết kế hệ thống ban đầu 1 đã đề xuất một kiến trúc cơ bản dựa trên mô hình Router-Solver kết hợp giữa RAG (Retrieval-Augmented Generation) và Text-to-SQL. Đây là một bước khởi đầu hợp lý, phản ánh các mô hình thiết kế phổ biến của năm 2023. Tuy nhiên, khi đối chiếu với các tiến bộ công nghệ tính đến năm 2025 và đặc thù ngữ nghĩa của tiếng Việt, hệ thống này bộc lộ những hạn chế về khả năng xử lý ngữ cảnh dài, độ chính xác trong truy xuất văn bản pháp luật và khả năng tự sửa lỗi (self-correction).
Báo cáo này, được xây dựng dựa trên sự tổng hợp của hơn 600 tài liệu nghiên cứu và điểm chuẩn kỹ thuật mới nhất, cung cấp một đánh giá chuyên sâu và đề xuất tái thiết kế kiến trúc hệ thống theo hướng Agentic RAG (RAG tác tử). Mục tiêu là chuyển đổi từ một chatbot hỏi-đáp thụ động sang một hệ thống tư vấn chủ động, có khả năng suy luận đa bước, tự kiểm chứng thông tin và xử lý các truy vấn phức tạp liên quan đến hồ sơ thí sinh và quy chế tuyển sinh. Bản báo cáo cũng cung cấp một lộ trình phát triển chi tiết kéo dài 16 tuần, tập trung vào việc giải quyết các thách thức cụ thể của dữ liệu tiếng Việt.
2. PHÂN TÍCH HIỆN TRẠNG VÀ CÁC ĐIỂM MÙ TRONG THIẾT KẾ BAN ĐẦU
2.1. Đánh Giá Thành Phần Router (Bộ Định Tuyến)
Trong thiết kế gốc 1, Router đóng vai trò phân loại ý định người dùng (Intent Classification) để điều hướng đến RAG Agent (xử lý văn bản) hoặc SQL Agent (xử lý số liệu). Thiết kế này đề xuất sử dụng SetFit hoặc Zero-shot LLM.
Phân tích chuyên sâu: Mặc dù SetFit là một giải pháp hiệu quả cho việc phân loại văn bản với ít dữ liệu huấn luyện (few-shot) 2, việc phụ thuộc hoàn toàn vào một mô hình phân loại tĩnh gặp phải hai vấn đề lớn trong ngữ cảnh tuyển sinh quân sự:
1.Độ trễ và Chi phí: Việc gọi một mô hình SetFit hoặc LLM cho mọi truy vấn, kể cả những truy vấn đơn giản, tạo ra độ trễ không cần thiết. Trong khi đó, các kỹ thuật như Semantic Router (định tuyến dựa trên ngữ nghĩa vector) có thể xử lý các truy vấn mẫu (ví dụ: "điểm chuẩn năm nay") với tốc độ dưới 10ms mà không cần suy luận mô hình phức tạp.4
2.Sự mơ hồ trong ý định hỗn hợp (Hybrid Intents): Các câu hỏi thực tế của thí sinh thường phức tạp, ví dụ: "Với 24 điểm khối A và là con thương binh hạng 2, tôi có đủ điều kiện vào Học viện Kỹ thuật Quân sự không và cần chuẩn bị giấy tờ gì?". Câu hỏi này yêu cầu cả truy xuất dữ liệu số (SQL - điểm chuẩn) và truy xuất văn bản (RAG - quy chế ưu tiên). Một bộ định tuyến phân loại đơn thuần sẽ khó có thể tách bóc ý định này một cách chính xác để điều phối cả hai tác tử cùng làm việc.6
Kiến nghị cải tiến: Chuyển đổi sang mô hình Semantic Router kết hợp Agent Supervisor. Semantic Router sẽ xử lý lớp đầu tiên cho các câu hỏi thường gặp (FAQ) để tối ưu tốc độ. Đối với các truy vấn phức tạp, thay vì chỉ phân loại, hệ thống cần một Supervisor Agent (Tác tử giám sát) sử dụng LLM để lập kế hoạch thực hiện (planning), quyết định gọi SQL Agent trước để lấy điểm, sau đó gọi RAG Agent để lấy thông tin ưu tiên, và cuối cùng tổng hợp câu trả lời.7
2.2. Đánh Giá Phân Hệ RAG (Xử Lý Văn Bản Pháp Quy)
Thiết kế hiện tại sử dụng Qdrant và BGE-M3 để tìm kiếm lai (Hybrid Search). Tuy nhiên, cách tiếp cận này chưa giải quyết triệt để vấn đề đặc thù của văn bản pháp luật Việt Nam.
Phân tích chuyên sâu:
●Vấn đề Chunking (Phân mảnh): Văn bản quy chế tuyển sinh thường có cấu trúc phân cấp sâu (Chương -> Điều -> Khoản -> Điểm). Các chiến lược phân mảnh văn bản thông thường (như Recursive Character Splitter) dựa trên số lượng ký tự thường cắt đứt mối liên kết ngữ nghĩa giữa các khoản mục. Ví dụ, một "Khoản 3" quy định về tiêu chuẩn mắt có thể bị tách khỏi "Điều 12" quy định về sức khỏe, khiến LLM mất ngữ cảnh khi chỉ truy xuất được đoạn văn bản chứa "Khoản 3" mà không biết nó thuộc Điều nào.9
●Mô hình Embedding: BGE-M3 là một mô hình đa ngôn ngữ mạnh, nhưng đối với các thuật ngữ pháp lý đặc thù của Việt Nam, các mô hình được tinh chỉnh riêng (fine-tuned) như Vietnamese_Embedding (dựa trên BGE-M3 nhưng huấn luyện trên 300.000 cặp dữ liệu tiếng Việt) hoặc ViRanker cho bước xếp hạng lại (reranking) đã chứng minh hiệu quả vượt trội hơn đáng kể trong các bài kiểm tra chuẩn (benchmark) như Legal Zalo.11
●Ảo giác (Hallucination): Trong lĩnh vực quân sự, thông tin sai lệch là không thể chấp nhận. Thiết kế RAG ngây thơ (Naive RAG) không có cơ chế tự kiểm tra. Các kỹ thuật như Corrective RAG (CRAG) hoặc Self-RAG là bắt buộc để hệ thống có thể tự đánh giá độ liên quan của tài liệu truy xuất được trước khi trả lời.14
2.3. Đánh Giá Phân Hệ SQL (Truy Xuất Dữ Liệu Thống Kê)
Thiết kế SQL Agent hiện tại dựa vào khả năng Zero-shot của LLM để viết câu lệnh SQL.
Phân tích chuyên sâu:
●Thách thức ngôn ngữ tiếng Việt: Dữ liệu trong PostgreSQL thường chứa tiếng Việt có dấu. Một truy vấn từ người dùng như "diem chuan hoc vien ky thuat quan su" (không dấu) sẽ không khớp (match) với dữ liệu "Học viện Kỹ thuật Quân sự" trong cơ sở dữ liệu nếu câu lệnh SQL được sinh ra không sử dụng các hàm xử lý ngôn ngữ như unaccent() hoặc pg_trgm (trigram similarity).15 Các LLM thông thường nếu không được hướng dẫn kỹ (prompt engineering) hoặc tinh chỉnh (fine-tuning) sẽ thường xuyên viết các câu lệnh WHERE school_name = '...' đơn giản và thất bại trong việc tìm kiếm.
●Độ phức tạp của lược đồ (Schema): Với nhiều bảng dữ liệu (điểm chuẩn, chỉ tiêu, khu vực), việc đưa toàn bộ lược đồ vào ngữ cảnh (context window) của LLM là không hiệu quả và dễ gây nhiễu. Cần có cơ chế Schema Filtering để chỉ chọn ra các bảng liên quan đến câu hỏi trước khi sinh SQL.17
3. KIẾN TRÚC ĐỀ XUẤT: HỆ THỐNG AGENTIC RAG ĐA TÁC TỬ (MULTI-AGENT)
Dựa trên phân tích trên, kiến trúc hệ thống được đề xuất nâng cấp từ mô hình đường ống tuyến tính (Linear Pipeline) sang mô hình đồ thị trạng thái (State Graph) sử dụng LangGraph.
3.1. Sơ Đồ Kiến Trúc Mức Cao (High-Level Architecture)
Hệ thống mới được tổ chức thành các Node (nút xử lý) và Edge (cạnh điều hướng) trong một đồ thị có trạng thái (Stateful Graph).

Thành phần	Công nghệ Đề xuất	Chức năng Nâng cao
Orchestrator	LangGraph Supervisor	Quản lý trạng thái hội thoại, lập kế hoạch đa bước, điều phối các Agent con, và duy trì bộ nhớ ngắn hạn/dài hạn.8
Intent Router	Semantic Router (BGE-M3)	Phân loại ý định siêu tốc (<10ms) dựa trên vector similarity, giảm tải cho LLM.4
Legal RAG Agent	CRAG (Corrective RAG)	Thực hiện quy trình: Truy xuất -> Tự đánh giá (Grader) -> Tìm kiếm bổ sung (nếu thiếu) -> Tổng hợp. Sử dụng ViRanker để rerank kết quả.13
Data SQL Agent	Dynamic Few-Shot SQL	Sử dụng pgvector để tìm các cặp câu hỏi-SQL mẫu tương tự nhằm hướng dẫn LLM viết SQL chính xác, xử lý tiếng Việt không dấu.20
LLM Core	Qwen2.5-7B-Instruct / vLLM	Mô hình ngôn ngữ nền tảng tối ưu cho tiếng Việt và tác vụ suy luận (reasoning), chạy trên hạ tầng vLLM để tối ưu thông lượng.22
Storage	PostgreSQL + Qdrant	PostgreSQL (lưu dữ liệu cấu trúc + checkpoint hội thoại), Qdrant (lưu vector văn bản + vector câu hỏi mẫu SQL).24
3.2. Chi Tiết Thiết Kế Các Tác Tử (Agents)
3.2.1. Legal RAG Agent với Chiến Lược Chunking Nhận Thức Cấu Trúc (Structure-Aware Chunking)
Để giải quyết vấn đề phân mảnh văn bản pháp luật, hệ thống không sử dụng bộ cắt ký tự (Character Splitter) thông thường. Thay vào đó, áp dụng chiến lược Structure-Aware Chunking 10:
1.Parsing: Sử dụng Regex hoặc Parser chuyên dụng để nhận diện các tiêu đề "Chương", "Điều", "Khoản".
2.Parent-Child Indexing: Mỗi đoạn văn bản nhỏ (Khoản) được lưu trữ kèm theo metadata chứa toàn bộ nội dung của cấp cha (Điều, Chương) hoặc ID của cấp cha. Khi truy xuất, hệ thống có thể trả về đoạn văn bản nhỏ để tính toán vector, nhưng khi đưa vào LLM thì đưa cả ngữ cảnh cấp cha (Parent Document Retrieval).
3.Corrective Flow: Sau khi truy xuất, một "Grader LLM" (phiên bản nhỏ như Qwen2.5-1.5B) sẽ chấm điểm độ liên quan. Nếu điểm thấp, hệ thống sẽ kích hoạt cơ chế tìm kiếm lại với từ khóa được viết lại (Query Rewriting) hoặc thông báo không có dữ liệu thay vì bịa đặt.14
3.2.2. SQL Agent với Cơ Chế Dynamic Few-Shot và Unaccent
SQL Agent được thiết kế để xử lý sự linh hoạt của ngôn ngữ tự nhiên tiếng Việt:
1.Dynamic Few-Shot Selector: Xây dựng một kho lưu trữ vector chứa 50-100 cặp (Câu hỏi tiếng Việt - Câu lệnh SQL chuẩn). Khi người dùng hỏi, hệ thống tìm 3 cặp tương đồng nhất để đưa vào prompt, giúp LLM học cách xử lý các trường hợp khó (ví dụ: cách tính điểm ưu tiên).28
2.Unaccent & Trigram: Prompt hệ thống được cấu hình để luôn sử dụng hàm unaccent() khi so sánh chuỗi văn bản. Ví dụ: WHERE unaccent(school_name) ILIKE unaccent('%nguyen hue%'). Điều này đảm bảo độ chính xác cao bất kể người dùng gõ có dấu hay không.15
3.Self-Correction: Nếu câu lệnh SQL bị lỗi khi thực thi, lỗi đó được đưa ngược lại vào LLM để tự sửa và chạy lại (tối đa 3 lần).
3.3. Mô Hình Ngôn Ngữ: Tại Sao Chọn Qwen2.5?
Dựa trên các bảng xếp hạng VMLU (Vietnamese Multitask Language Understanding) mới nhất năm 2025 30, Qwen2.5-7B-Instruct hiện là mô hình mã nguồn mở dưới 10B tham số có hiệu năng tốt nhất trên tiếng Việt, vượt qua cả Vistral-7B và Llama-3-8B trong các tác vụ STEM và Xã hội.
●Điểm số VMLU: Qwen2.5-7B đạt trung bình 57.51, trong khi Vistral-7B đạt thấp hơn ở các tác vụ suy luận phức tạp.
●Context Window: Hỗ trợ 128k token, cho phép đưa nhiều văn bản quy chế vào ngữ cảnh mà không bị cắt ngắn.23
●Hỗ trợ vLLM: Qwen2.5 tương thích hoàn toàn với vLLM, cho phép triển khai sản xuất với tốc độ token/s cao gấp 3-4 lần so với Ollama.32
4. LỘ TRÌNH PHÁT TRIỂN CHI TIẾT (16 TUẦN)
Lộ trình này được mở rộng từ 7 tuần lên 16 tuần để đảm bảo tính thực tiễn, bao gồm thời gian cho việc chuẩn bị dữ liệu kỹ lưỡng và đánh giá khắt khe (Red Teaming) trước khi triển khai.
Giai Đoạn 1: Nền Tảng Dữ Liệu và Hạ Tầng (Tuần 1 - 4)
Mục tiêu: Xây dựng kho dữ liệu sạch, có cấu trúc và thiết lập môi trường vector database tối ưu.
●Tuần 1: Thiết kế Cơ Sở Dữ Liệu Quan Hệ (PostgreSQL)
○Cài đặt PostgreSQL 16 với các extension: pgvector, pg_trgm, unaccent.
○Thiết kế Schema chuẩn hóa cho dữ liệu tuyển sinh (bảng truong, nganh, diem_chuan, tieu_chi_phu).
○Quan trọng: Tạo các View phẳng (Flattened Views) để đơn giản hóa việc truy vấn cho SQL Agent. Ví dụ: view_diem_chuan_full kết nối sẵn tên trường, mã ngành và điểm.1
●Tuần 2: Xử Lý Dữ Liệu Văn Bản Pháp Quy (Advanced ETL)
○Thu thập toàn bộ Thông tư, Quy chế tuyển sinh quân sự 2024-2025.
○Phát triển script Python để thực hiện Structure-Aware Chunking: Tách văn bản dựa trên regex của các điều khoản luật, giữ lại metadata (Chương, Điều).
○Sử dụng mô hình embedding AITeamVN/Vietnamese_Embedding để vector hóa dữ liệu và nạp vào Qdrant.11
●Tuần 3: Tinh Chỉnh Mô Hình Reranker và Router
○Triển khai ViRanker 13 dưới dạng một microservice (sử dụng Docker) để phục vụ việc xếp hạng lại kết quả tìm kiếm.
○Xây dựng bộ dữ liệu huấn luyện cho Semantic Router: Tổng hợp 1000+ câu hỏi mẫu về tuyển sinh, gán nhãn ý định (Intent Labeling).
○Tạo index vector cho Semantic Router để đảm bảo độ trễ định tuyến <10ms.
●Tuần 4: Thiết Lập Môi Trường LLM Serving
○Cài đặt và cấu hình vLLM trên máy chủ GPU. So sánh hiệu năng với Ollama để xác nhận cấu hình tối ưu (Batch size, GPU memory utilization).32
○Tải và kiểm thử mô hình Qwen2.5-7B-Instruct và Qwen2.5-Coder-7B (cho SQL).
Giai Đoạn 2: Phát Triển Các Tác Tử Chuyên Biệt (Tuần 5 - 8)
Mục tiêu: Xây dựng từng tác tử chức năng với khả năng hoạt động độc lập chính xác.
●Tuần 5: Xây Dựng SQL Agent với Dynamic Few-Shot
○Tạo kho dữ liệu "Golden SQL Queries": 50 cặp câu hỏi-SQL mẫu bao quát các trường hợp khó (so sánh điểm, tính toán chênh lệch, lọc theo khu vực).
○Tích hợp quy trình Dynamic Few-Shot vào LangChain/LangGraph: Khi nhận câu hỏi -> Tìm 3 ví dụ mẫu -> Tạo Prompt -> Sinh SQL -> Thực thi.20
○Kiểm thử khả năng xử lý tiếng Việt không dấu.
●Tuần 6: Phát Triển Legal RAG Agent (CRAG)
○Xây dựng đồ thị CRAG trong LangGraph:
■Node Retrieve: Gọi Qdrant.
■Node Grade: Dùng LLM đánh giá độ liên quan (Yes/No/Ambiguous).
■Node Generate: Sinh câu trả lời có trích dẫn nguồn (Citation).27
○Tích hợp ViRanker vào bước sau Retrieve để lọc nhiễu.
●Tuần 7: Xây Dựng Supervisor Agent
○Thiết kế System Prompt cho Supervisor: Định nghĩa rõ vai trò, công cụ và quy trình ra quyết định.
○Cài đặt logic quản lý trạng thái hội thoại (Conversation State): Lưu trữ lịch sử chat, thông tin thí sinh đã trích xuất (Entity Extraction) vào bộ nhớ đệm (Redis hoặc Postgres Checkpointer).19
●Tuần 8: Tích Hợp Hệ Thống (Integration)
○Ghép nối Supervisor với SQL Agent và RAG Agent.
○Xây dựng API Gateway (FastAPI) để lộ diện endpoint cho giao diện người dùng.
○Thực hiện các kịch bản kiểm thử tích hợp (End-to-End Testing) với các câu hỏi phức tạp (Hybrid Queries).
Giai Đoạn 3: Đánh Giá, Tối Ưu và Triển Khai (Tuần 9 - 12)
Mục tiêu: Đảm bảo độ tin cậy và hiệu năng trước khi ra mắt.
●Tuần 9: Thiết Lập Khung Đánh Giá RAGAS
○Tạo bộ dữ liệu kiểm thử tổng hợp (Synthetic Test Set) sử dụng LLM để sinh ra các cặp câu hỏi-câu trả lời từ tài liệu gốc (Question Generation).37
○Cài đặt RAGAS để đo lường các chỉ số: Faithfulness (Độ trung thực), Answer Relevancy (Độ liên quan), Context Recall (Khả năng tìm lại thông tin).39
○Chạy đánh giá định lượng trên toàn bộ hệ thống.
●Tuần 10: Tối Ưu Hóa Hiệu Năng (Performance Tuning)
○Phân tích các trường hợp thất bại (Failure Analysis) từ báo cáo RAGAS.
○Tinh chỉnh tham số: Số lượng chunk truy xuất (Top-k), ngưỡng điểm reranking, và prompt của Supervisor.
○Tối ưu hóa cơ sở dữ liệu: Tạo thêm index cho PostgreSQL, tinh chỉnh HNSW parameters cho Qdrant để cân bằng giữa tốc độ và độ chính xác (Recall).24
●Tuần 11: Phát Triển Giao Diện và Human-in-the-Loop
○Xây dựng giao diện người dùng (UI) hỗ trợ hiển thị luồng suy nghĩ (Chain of Thought) của Agent để tăng tính minh bạch.
○Tích hợp cơ chế Human-in-the-Loop: Cho phép chuyên gia can thiệp hoặc sửa lại câu trả lời trong giai đoạn thử nghiệm để Agent học hỏi (Reinforcement Learning from Human Feedback - RLHF dạng đơn giản).41
●Tuần 12: Đóng Gói và Triển Khai (Deployment)
○Đóng gói toàn bộ hệ thống bằng Docker Compose.
○Thiết lập quy trình CI/CD.
○Viết tài liệu hướng dẫn vận hành và bảo trì.
Giai Đoạn 4: Mở Rộng và Nâng Cao (Tuần 13 - 16)
●Tuần 13-16: Theo dõi hoạt động thực tế, thu thập log phản hồi của người dùng để tiếp tục tinh chỉnh bộ dữ liệu Few-shot và Semantic Router. Nghiên cứu khả năng nâng cấp lên mô hình Qwen2.5-14B hoặc DeepSeek-R1 nếu tài nguyên phần cứng cho phép để tăng cường khả năng suy luận sâu.
5. CÁC CHIẾN LƯỢC KỸ THUẬT CỐT LÕI (TECHNICAL DEEP DIVE)
5.1. Chiến Lược Embedding và Reranking Cho Tiếng Việt
Việc lựa chọn mô hình embedding là yếu tố sống còn. Nghiên cứu 11 chỉ ra rằng Vietnamese_Embedding (finetune từ BGE-M3) đạt hiệu suất cao nhất hiện nay cho tác vụ truy xuất văn bản tiếng Việt, vượt qua cả các mô hình đa ngôn ngữ gốc.
●Kiến nghị: Sử dụng Vietnamese_Embedding cho việc mã hóa (encoding) văn bản quy chế và câu hỏi người dùng.
●Reranking: Sử dụng ViRanker 13 là bước bắt buộc. Trong các hệ thống RAG pháp lý, bước truy xuất đầu tiên (Retrieval) thường trả về nhiều tài liệu nhiễu. Reranker hoạt động như một bộ lọc tinh, so sánh trực tiếp câu hỏi và đoạn văn bản để đẩy các kết quả phù hợp nhất lên đầu, giúp LLM không bị "ngộ độc" ngữ cảnh.
5.2. Kỹ Thuật Dynamic Few-Shot Prompting Cho SQL
Thay vì nhồi nhét hàng chục ví dụ SQL vào prompt (gây tốn token và giảm khả năng chú ý của mô hình), kỹ thuật Dynamic Few-Shot hoạt động như sau:
1.Lưu trữ: Lưu 100 ví dụ SQL chuẩn vào Qdrant. Mỗi ví dụ gồm: Metadata: {question: "..."}, Vector: embedding(question), Payload: {sql: "..."}.
2.Truy vấn: Khi user hỏi câu A, hệ thống vector search tìm 3 câu hỏi mẫu gần nhất với A trong Qdrant.
3.Prompt Construction: Hệ thống ghép 3 câu SQL mẫu tìm được vào Prompt gửi cho LLM.
4.Kết quả: LLM "học" được cách giải quyết vấn đề tương tự ngay tại thời điểm đó (In-Context Learning), giúp tăng độ chính xác lên đáng kể so với Static Prompting.20
5.3. Quản Lý Trạng Thái Với LangGraph Checkpointer
Trong môi trường chatbot, người dùng thường hỏi nối tiếp (follow-up). Ví dụ: "Trường lục quân 1 lấy bao nhiêu điểm?" -> "Thế còn lục quân 2?".
Để Supervisor hiểu "Thế còn..." ám chỉ "Điểm chuẩn", hệ thống cần bộ nhớ. LangGraph cung cấp PostgresSaver để lưu trữ toàn bộ trạng thái (state) của đồ thị vào PostgreSQL sau mỗi bước nhảy (node transition). Điều này cho phép:
●Duy trì ngữ cảnh qua các lượt hội thoại dài.
●Khả năng "Time Travel": Quay lại trạng thái trước đó để sửa lỗi nếu Agent đi sai hướng.
●Phục hồi phiên làm việc nếu hệ thống bị khởi động lại.19
-- 1. KÍCH HOẠT CÁC EXTENSION QUAN TRỌNG
-- Hỗ trợ tìm kiếm vector cho RAG sau này
CREATE EXTENSION IF NOT EXISTS vector;
-- Hỗ trợ tìm kiếm mờ (fuzzy search) cho tên trường/ngành
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Hỗ trợ tìm kiếm tiếng Việt không dấu (quan trọng cho người dùng Việt Nam)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- 2. TẠO BẢNG DỮ LIỆU (TABLES)

-- Bảng danh sách các trường quân đội
CREATE TABLE IF NOT EXISTS truong (
    school_id VARCHAR(20) PRIMARY KEY, -- Ví dụ: HVKTQS
    school_name TEXT NOT NULL,         -- Ví dụ: Học viện Kỹ thuật Quân sự
    alias TEXT,                      -- Tên gọi khác: {'MTA', 'Học viện Kỹ thuật'}
    location VARCHAR(50),              -- Ví dụ: Miền Bắc, Miền Nam
    website TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng danh mục ngành đào tạo
CREATE TABLE IF NOT EXISTS nganh (
    major_code VARCHAR(20) PRIMARY KEY, -- Ví dụ: 7480201
    major_name TEXT NOT NULL,           -- Ví dụ: Công nghệ thông tin
    description TEXT                    -- Mô tả ngắn về ngành
);

-- Bảng khối thi (A00, A01...)
CREATE TABLE IF NOT EXISTS khoi_thi (
    block_code VARCHAR(10) PRIMARY KEY,
    subjects TEXT NOT NULL              -- Ví dụ: Toán, Lý, Hóa
);

-- Bảng dữ liệu điểm chuẩn (Fact Table)
CREATE TABLE IF NOT EXISTS diem_chuan (
    id SERIAL PRIMARY KEY,
    school_id VARCHAR(20) REFERENCES truong(school_id),
    major_code VARCHAR(20) REFERENCES nganh(major_code),
    block_code VARCHAR(10) REFERENCES khoi_thi(block_code),
    year INTEGER NOT NULL,              -- Năm tuyển sinh: 2023, 2024
    gender VARCHAR(10) CHECK (gender IN ('NAM', 'NU', 'CHUNG')), -- Giới tính
    region VARCHAR(20) CHECK (region IN ('MIEN_BAC', 'MIEN_NAM', 'TOAN_QUOC')), -- Khu vực
    score DECIMAL(4,2) NOT NULL,        -- Điểm chuẩn: 25.55
    tieu_chi_phu TEXT,                  -- Tiêu chí phụ (nếu có)
    ghi_chu TEXT,
    UNIQUE (school_id, major_code, block_code, year, gender, region) -- Tránh trùng lặp
);

-- 3. TẠO INDEX ĐỂ TỐI ƯU TỐC ĐỘ TÌM KIẾM

-- Index hỗ trợ tìm kiếm tên trường không dấu nhanh chóng
CREATE INDEX idx_truong_name_trgm ON truong USING GIN (unaccent(school_name) gin_trgm_ops);
-- Index cho việc lọc điểm chuẩn theo năm và trường
CREATE INDEX idx_diem_chuan_filter ON diem_chuan (year, school_id, score);

-- 4. TẠO VIEW PHẲNG (FLATTENED VIEWS) CHO AI AGENT
-- Mục đích: Giúp SQL Agent chỉ cần query vào bảng này là có đủ thông tin, 
-- không cần tự viết lệnh JOIN phức tạp dễ gây lỗi.

CREATE OR REPLACE VIEW view_tra_cuu_diem AS
SELECT 
    d.year AS nam,
    t.school_name AS truong,
    t.school_id AS ma_truong,
    n.major_name AS nganh,
    k.block_code AS khoi,
    d.gender AS gioi_tinh,
    d.region AS khu_vuc,
    d.score AS diem_chuan,
    d.tieu_chi_phu
FROM diem_chuan d
JOIN truong t ON d.school_id = t.school_id
LEFT JOIN nganh n ON d.major_code = n.major_code
LEFT JOIN khoi_thi k ON d.block_code = k.block_code;

-- 5. DỮ LIỆU MẪU (SEED DATA) ĐỂ TEST

INSERT INTO truong (school_id, school_name, location) VALUES 
('MTA', 'Học viện Kỹ thuật Quân sự', 'Miền Bắc'),
('SQL', 'Trường Sĩ quan Lục quân 1', 'Miền Bắc');

INSERT INTO nganh (major_code, major_name) VALUES 
('CNTT', 'Công nghệ thông tin'),
('CK', 'Kỹ thuật Cơ khí');

INSERT INTO khoi_thi (block_code, subjects) VALUES 
('A00', 'Toán, Lý, Hóa'), 
('A01', 'Toán, Lý, Anh');

INSERT INTO diem_chuan (school_id, major_code, block_code, year, gender, region, score) VALUES 
('MTA', 'CNTT', 'A00', 2024, 'NAM', 'MIEN_BAC', 26.5),
('MTA', 'CNTT', 'A01', 2024, 'NAM', 'MIEN_BAC', 26.0),
('SQL', 'CK', 'A00', 2024, 'NAM', 'MIEN_BAC', 24.5);