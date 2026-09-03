import sys
import datetime
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add the project root to sys.path so we can import internal modules
sys.path.insert(0, str(Path(__file__).parent))

from knowledge.knowledge_manager import KnowledgeManager

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def ingest_markdown(filepath: Path, base_topic: str):
    log(f"Dang doc file: {filepath.name}")
    content = filepath.read_text(encoding="utf-8")
    
    # Split by level-2 headers
    sections = content.split("\n## ")
    if not sections:
        return
        
    db = KnowledgeManager()
    
    # sections[0] is usually the title/intro
    count = 0
    for section in sections[1:]:
        lines = section.strip().split("\n", 1)
        if len(lines) < 2:
            continue
            
        sub_topic = lines[0].strip()
        body = lines[1].strip()
        
        full_topic = f"{base_topic}: {sub_topic}"
        
        # Insert into knowledge db directly with confidence 1.0
        db.add_knowledge(
            topic=full_topic,
            content=body,
            confidence=1.0,
            source=filepath.name
        )
        log(f"  + Da luu: {full_topic}")
        count += 1
        
    log(f"=> Hoan thanh {filepath.name}. Da luu {count} muc kien thuc.\n")

if __name__ == "__main__":
    base_dir = Path(__file__).parent
    dsa_file = base_dir / "data" / "docs" / "dsa" / "Python_DSA_Core.md"
    sql_file = base_dir / "data" / "docs" / "sql" / "SQL_Database_Core.md"
    
    log("=== BAT DAU NAP KIEN THUC DSA PYTHON & SQL ===")
    
    if dsa_file.exists():
        ingest_markdown(dsa_file, "DSA Python")
    else:
        log("Khong tim thay file DSA!")
        
    if sql_file.exists():
        ingest_markdown(sql_file, "SQL Database")
    else:
        log("Khong tim thay file SQL!")
        
    log("=== DA NAP XONG KIEN THUC VAO KNOWLEDGE DB ===")
