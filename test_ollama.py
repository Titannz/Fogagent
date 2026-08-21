"""End-to-End integration verification for Memory, Knowledge, and Study Mode."""
import sys
from agent.agent import Agent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    agent = Agent()
    print("=== FogAgent E2E Verification ===")
    print(f"Initial Status: {agent.get_status()}")

    # 1. Test Memory
    print("\n1. Storing memory fact 'user_nickname: Titan'...")
    agent.memory_mgr.remember_fact("user_nickname", "Titan", category="profile")
    print(f"Recalled: {agent.memory_mgr.recall_fact('user_nickname')}")

    # 2. Test Study Mode ON
    print("\n2. Enabling Study Mode...")
    print(agent.enable_study())

    print("\n3. Teaching Agent a new concept...")
    teach_prompt = "QLoRA is an efficient fine-tuning approach that quantizes a pre-trained model to 4-bit, then adds small trainable Low Rank Adaptation weights."
    print("Streaming response:")
    for chunk in agent.run_stream(teach_prompt):
        print(chunk, end="", flush=True)
    print()

    # 3. Test Study Mode OFF
    print("\n4. Disabling Study Mode...")
    print(agent.disable_study())

    # 4. Verify Knowledge retrieval
    print(f"\nKnowledge records in DB: {agent.knowledge_mgr.count_knowledge()}")
    for k in agent.knowledge_mgr.list_all():
        print(f" - [{k['topic']}]: {k['content']} (Confidence: {k['confidence']})")

    # 5. Query Agent using learned knowledge & memory
    print("\n5. Querying agent about Titan and QLoRA...")
    for chunk in agent.run_stream("What is my nickname, and what is QLoRA? Answer briefly."):
        print(chunk, end="", flush=True)
    print("\n\n=== Verification Finished Successfully ===")

if __name__ == "__main__":
    main()
