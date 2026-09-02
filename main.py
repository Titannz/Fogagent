"""FogAgent Main Entrypoint & CLI Interface with Data Quality & Loop Control."""
import sys
from agent.agent import Agent

# Ensure standard output supports UTF-8 on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


def print_banner():
    print("==========================================================")
    print("             FogAgent v0.6 - Controlled Local AI          ")
    print("==========================================================")
    print("Lệnh cơ bản:")
    print("  youcanstudy          - Bật chế độ học tập có kiểm soát")
    print("  byebye               - Tắt chế độ học tập (giữ nguyên tri thức)")
    print("  status               - Xem trạng thái Agent, GPU và số lượng bản ghi")
    print("  exit / quit          - Thoát chương trình")
    print("\nKiểm soát Tri thức & Hàng đợi (Data Quality & Queue):")
    print("  queue                - Xem danh sách tài liệu đang chờ học")
    print("  study_now <id>       - Bắt đầu học 1 bài cụ thể trong hàng đợi")
    print("  queue_drop <id>      - Xóa 1 bài khỏi hàng đợi")
    print("  audit                - Quét kiểm tra dữ liệu rác, trùng lặp trong CSDL")
    print("  delete <id>          - Xóa vĩnh viễn 1 bản ghi tri thức")
    print("  knowledge            - Liệt kê toàn bộ tri thức đã lưu")
    print("\nKý ức & Cá nhân hóa (Memory & Profile):")
    print("  profile              - Xem hồ sơ cá nhân hóa & quy tắc kiểm soát")
    print("  remember <k>: <v>    - Lưu thủ công 1 sở thích hoặc thông tin cá nhân")
    print("  memories             - Liệt kê toàn bộ ký ức cá nhân")
    print("==========================================================")


def handle_approval_gate(agent: Agent, candidate: dict) -> None:
    """Display extracted knowledge and wait for explicit human confirmation before saving."""
    print("\n┌── [XÁC NHẬN TRI THỨC MỚI] ──────────────────────────────┐")
    print(f"│ • Chủ đề: {candidate.get('topic', 'N/A')}")
    print(f"│ • Nội dung: {candidate.get('content', 'N/A')}")
    print(f"│ • Độ tin cậy: {candidate.get('confidence', 0.0):.2f}")
    if candidate.get("tags"):
        print(f"│ • Thẻ (Tags): {', '.join(candidate.get('tags', []))}")
    if candidate.get("duplicate_msg"):
        print(f"│ • Tình trạng: {candidate.get('duplicate_msg')}")
    print("└─────────────────────────────────────────────────────────┘")

    while True:
        choice = input("👉 Bạn có đồng ý lưu tri thức này vào CSDL không? (y/n): ").strip().lower()
        if choice == "y":
            rec_id = agent.commit_study_candidate(candidate)
            print(f"✅ Đã lưu thành công vào CSDL với ID #{rec_id}!\n")
            break
        elif choice == "n":
            print("❌ Đã hủy bỏ. Không lưu vào CSDL.\n")
            break
        else:
            print("Vui lòng chỉ nhập 'y' (Đồng ý) hoặc 'n' (Từ chối).")


def main():
    agent = Agent()
    print_banner()

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting FogAgent. Goodbye!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("exit", "quit"):
            print("\nGoodbye!")
            break

        if cmd == "help":
            print_banner()
            continue

        if cmd == "youcanstudy":
            print(f"\nFogAgent: {agent.enable_study()}")
            continue

        if cmd == "byebye":
            print(f"\nFogAgent: {agent.disable_study()}")
            continue

        if cmd == "status":
            status = agent.get_status()
            print("\n--- FogAgent Status ---")
            for k, v in status.items():
                print(f"  {k}: {v}")
            print("-----------------------")
            continue

        if cmd == "profile":
            memories = agent.memory_mgr.list_memories()
            print(f"\n--- Hồ sơ cá nhân hóa ({len(memories)} mục) ---")
            if not memories:
                print("  (Chưa có thông tin cá nhân hóa)")
            for m in memories:
                print(f"  [{m['category']}] {m['key']}: {m['value']}")
            print("---------------------------------------------")
            continue

        if cmd == "memories":
            memories = agent.memory_mgr.list_memories()
            print(f"\n--- Stored Memories ({len(memories)}) ---")
            if not memories:
                print("  (No memories recorded yet)")
            for m in memories:
                print(f"  [{m['category']}] {m['key']}: {m['value']}")
            print("---------------------------------")
            continue

        if cmd == "knowledge":
            knowledge_list = agent.knowledge_mgr.list_all()
            print(f"\n--- Stored Knowledge ({len(knowledge_list)}) ---")
            if not knowledge_list:
                print("  (No knowledge learned yet)")
            for k in knowledge_list:
                print(f"  * #{k['id']} [{k['topic']}] (Confidence: {k['confidence']:.2f})")
                print(f"    Content: {k['content']}")
                if k['tags']:
                    print(f"    Tags: {k['tags']}")
            print("---------------------------------")
            continue

        if cmd == "queue":
            pending = agent.study_queue.get_pending()
            print(f"\n--- Hàng đợi học tập ({len(pending)} bài chờ) ---")
            if not pending:
                print("  (Hàng đợi trống)")
            for p in pending:
                print(f"  * [ID #{p['id']}] {p['title']} (Dự kiến: ~{p['estimated_seconds']}s)")
                print(f"    Nội dung: {p['content'][:120]}...")
            print("-----------------------------------------------")
            continue

        if cmd.startswith("study_now "):
            raw_id = cmd[len("study_now "):].strip()
            if raw_id.isdigit():
                qid = int(raw_id)
                item = agent.study_queue.get_item(qid)
                if not item:
                    print(f"\nKhông tìm thấy bài học ID #{qid} trong hàng đợi.")
                    continue
                print(f"\n[Bắt đầu học bài ID #{qid}]: {item['title']}")
                candidate = agent.extract_study_candidate(item['content'], source=f"queue_{qid}")
                if candidate:
                    handle_approval_gate(agent, candidate)
                    agent.study_queue.mark_completed(qid)
                else:
                    print("Không trích xuất được tri thức hợp lệ hoặc nội dung bị từ chối.")
                continue

        if cmd.startswith("queue_drop "):
            raw_id = cmd[len("queue_drop "):].strip()
            if raw_id.isdigit():
                qid = int(raw_id)
                if agent.study_queue.remove_item(qid):
                    print(f"\n✅ Đã xóa bài ID #{qid} khỏi hàng đợi.")
                else:
                    print(f"\nKhông tìm thấy bài ID #{qid} trong hàng đợi.")
                continue

        if cmd == "audit":
            report = agent.knowledge_mgr.audit_data()
            print("\n--- Báo cáo kiểm định dữ liệu (Audit Report) ---")
            print(f"  Tổng số bản ghi: {report['total_records']}")
            print(f"  Bản ghi độ tin cậy thấp (< 0.85): {report['low_confidence_count']}")
            print(f"  Chủ đề bị trùng lặp: {report['duplicate_topics_count']}")
            if report['duplicate_topics']:
                for t, ids in report['duplicate_topics'].items():
                    print(f"    • Chủ đề '{t}': các ID {ids}")
            print("-------------------------------------------------")
            continue

        if cmd.startswith("delete "):
            raw_id = cmd[len("delete "):].strip()
            if raw_id.isdigit():
                kid = int(raw_id)
                if agent.knowledge_mgr.delete_knowledge(kid):
                    print(f"\n✅ Đã xóa vĩnh viễn bản ghi tri thức #{kid}.")
                else:
                    print(f"\nKhông tìm thấy bản ghi tri thức #{kid}.")
                continue

        if cmd.startswith("remember ") and ":" in user_input:
            parts = user_input[len("remember "):].split(":", 1)
            k = parts[0].strip()
            v = parts[1].strip()
            if k and v:
                agent.memory_mgr.remember_fact(k, v, category="preference")
                print(f"\nFogAgent: Đã ghi nhớ sở thích '{k}': '{v}'")
                continue

        # Study Mode workload check for long content
        if agent.study_mode:
            workload = agent.estimate_workload(user_input)
            if workload["is_long_task"]:
                print("\n┌── [DỰ TÍNH TÁC VỤ HỌC TẬP] ──────────────────────────────┐")
                print(f"│ • Khối lượng: ~{workload['word_count']} từ (~{workload['estimated_tokens']} tokens)")
                print(f"│ • Dự kiến thời gian: ~{workload['estimated_seconds']}s trên GPU Radeon 780M")
                print(f"│ • Cảnh báo: Tác vụ dài có thể làm máy ấm lên.")
                print("└──────────────────────────────────────────────────────────┘")
                choice = input("👉 Bạn có muốn bắt đầu học ngay bây giờ không? (y/n): ").strip().lower()
                if choice != "y":
                    print("\nBạn chọn KHÔNG học ngay. Bạn muốn:")
                    print("  [1] Lưu vào Hàng Đợi (Study Queue) để học sau")
                    print("  [2] Hủy bỏ hoàn toàn")
                    sub_choice = input("Lựa chọn của bạn (1/2): ").strip()
                    if sub_choice == "1":
                        title = user_input[:40].replace("\n", " ") + "..."
                        qid = agent.queue_study_item(title=title, content=user_input, estimated_seconds=workload["estimated_seconds"])
                        print(f"✅ Đã lưu vào Hàng Đợi [ID #{qid}]. Dùng 'study_now {qid}' để học khi máy mát.")
                    else:
                        print("❌ Đã hủy bỏ hoàn toàn tác vụ.")
                    continue

        # Normal generation
        try:
            print("\nFogAgent: ", end="", flush=True)
            for chunk in agent.run_stream(user_input):
                print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(f"\n[Error] {e}")

        # Human Approval Gate if candidate was extracted in Study Mode
        if agent.study_mode:
            try:
                candidate = agent.extract_study_candidate(user_input)
                if candidate:
                    handle_approval_gate(agent, candidate)
            except Exception as e:
                print(f"\n[Study Notice] Không thể phân tích tri thức: {e}")


if __name__ == "__main__":
    main()
