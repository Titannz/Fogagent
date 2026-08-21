"""FogAgent Main Entrypoint & CLI Interface."""
import sys
from agent.agent import Agent

# Ensure standard output supports UTF-8 on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


def print_banner():
    print("================================")
    print("        FogAgent v0.5")
    print("        Local AI Agent")
    print("================================")
    print("Commands:")
    print("  youcanstudy          - Enable Study Mode (allow learning)")
    print("  byebye               - Disable Study Mode (stop learning)")
    print("  remember <k>: <v>    - Explicitly save a memory fact")
    print("  memories             - List all stored memories")
    print("  knowledge            - List all learned knowledge")
    print("  status               - Show Agent Status")
    print("  exit                 - Quit")
    print("================================")


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

        if cmd.startswith("remember ") and ":" in user_input:
            parts = user_input[len("remember "):].split(":", 1)
            k = parts[0].strip()
            v = parts[1].strip()
            if k and v:
                agent.memory_mgr.remember_fact(k, v)
                print(f"\nFogAgent: Remembered '{k}': '{v}'")
                continue

        if cmd == "help":
            print_banner()
            continue

        try:
            print("\nFogAgent: ", end="", flush=True)
            for chunk in agent.run_stream(user_input):
                print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(f"\n[Error] {e}")


if __name__ == "__main__":
    main()
