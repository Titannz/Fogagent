"""Controlled Math Study Runner with 1-Hour Time Limit and Thermal Throttling Protection."""
import sys
import time
import datetime
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pypdf import PdfReader
from config.settings import settings
from models.ollama_model import OllamaModel
from knowledge.knowledge_manager import KnowledgeManager
from knowledge.data_cleaner import DataCleaner
from agent.study_engine import StudyEngine

MAX_DURATION_SECONDS = 3600  # Exactly 1 hour

MATH_FILES = [
    {"name": "Matrix.pdf", "topic": "Đại số tuyến tính: Ma trận & Định thức"},
    {"name": "Mean_value_theorem.pdf", "topic": "Giải tích: Định lý giá trị trung bình (Rolle, Lagrange, Cauchy)"},
    {"name": "DaySo.pdf", "topic": "Giải tích: Dãy số & Giới hạn"},
]

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def main():
    start_time = time.time()
    log("=== BẮT ĐẦU PHIÊN HỌC TẬP CÓ KIỂM SOÁT (THỜI LƯỢNG TỐI ĐA: 1 GIỜ) ===")
    log(f"Mục tiêu: Bóc tách định nghĩa, định lý, công thức sạch từ 3 tài liệu Toán Đại Học.")
    log(f"Giới hạn: Tự động dừng sau 3600 giây (1h) hoặc khi hoàn thành tài liệu.\n")

    docs_dir = settings.data_dir / "docs" / "math"
    knowledge_mgr = KnowledgeManager()
    cleaner = DataCleaner(min_confidence=0.85, min_words=5)
    llm = OllamaModel()
    study_engine = StudyEngine(llm=llm, knowledge_mgr=knowledge_mgr, cleaner=cleaner)

    total_learned = 0
    pages_processed = 0

    for doc_info in MATH_FILES:
        elapsed = time.time() - start_time
        if elapsed >= MAX_DURATION_SECONDS:
            log("⏱️ Đã chạm mốc 1 giờ! Tự động dừng phiên học tập an toàn.")
            break

        file_path = docs_dir / doc_info["name"]
        if not file_path.exists():
            log(f"⚠️ Không tìm thấy file: {file_path}")
            continue

        log(f"📘 Bắt đầu nghiên cứu: {doc_info['name']} ({doc_info['topic']})")
        try:
            reader = PdfReader(str(file_path))
            total_pages = len(reader.pages)
        except Exception as e:
            log(f"Lỗi đọc PDF {doc_info['name']}: {e}")
            continue

        for page_idx in range(total_pages):
            elapsed = time.time() - start_time
            if elapsed >= MAX_DURATION_SECONDS:
                log("⏱️ Đã chạm mốc 1 giờ! Dừng lại ngay lập tức theo lệnh.")
                break

            page_num = page_idx + 1
            raw_text = reader.pages[page_idx].extract_text() or ""
            raw_text = raw_text.strip()

            # Skip short or empty pages
            if len(raw_text.split()) < 30:
                continue

            # Process in manageable chunks of ~200-400 words
            words = raw_text.split()
            chunk_size = 250
            for i in range(0, len(words), chunk_size):
                if time.time() - start_time >= MAX_DURATION_SECONDS:
                    break

                chunk_text = " ".join(words[i:i + chunk_size])
                if cleaner.is_noise_or_trivial(chunk_text):
                    continue

                source_tag = f"{doc_info['name']} (Trang {page_num})"
                try:
                    candidate = study_engine.evaluate_and_extract(chunk_text, source=source_tag)
                    if candidate and candidate.get("duplicate_status") == "NEW":
                        rec_id = study_engine.commit_knowledge(candidate)
                        total_learned += 1
                        log(f"  ✅ [Đã học #{rec_id}]: {candidate['topic']} (Tin cậy: {candidate['confidence']:.2f})")
                    elif candidate and candidate.get("duplicate_status") == "DUPLICATE":
                        log(f"  ℹ️ [Trùng lặp - Bỏ qua]: {candidate['topic']}")
                except Exception as e:
                    log(f"  ⚠️ Lỗi bóc tách đoạn text: {e}")

                # Small cooldown (3s) to prevent GPU thermal spike
                time.sleep(3)

            pages_processed += 1
            # Cooldown every 3 pages
            if pages_processed % 3 == 0:
                log(f"  ❄️ Nghỉ 6 giây tản nhiệt GPU (Đã xử lý {pages_processed} trang)...")
                time.sleep(6)

    total_time = int(time.time() - start_time)
    minutes = total_time // 60
    seconds = total_time % 60
    log(f"\n=== KẾT THÚC PHIÊN HỌC TẬP ===")
    log(f"Thời gian hoạt động: {minutes} phút {seconds} giây.")
    log(f"Số trang đã phân tích: {pages_processed}")
    log(f"Tổng số tri thức sạch mới được lưu vào CSDL: {total_learned}")
    log(f"Tổng số bản ghi hiện có trong Knowledge Base: {knowledge_mgr.count_knowledge()}")

if __name__ == "__main__":
    main()
