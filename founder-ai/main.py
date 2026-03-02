# import os
# import sys
# import io

# # Fix Windows terminal encoding for emojis/special chars
# if sys.platform == "win32":
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# from config import GEMINI_API_KEY, OUTPUT_DIR
# from agents import planner_agent, executor_agent, decision_agent, generate_final_strategy, C


# def save_file(filename, content):
#     """Save content to output/ folder."""
#     path = os.path.join(OUTPUT_DIR, filename)
#     with open(path, "w", encoding="utf-8") as f:
#         f.write(content)
#     return path


# def main():
#     # ---- Header ----
#     print(f"\n{C.BOLD}{C.CYAN}")
#     print("╔══════════════════════════════════════════════╗")
#     print("║     🚀 FOUNDER AI - Startup Strategy        ║")
#     print("║     Simple Python | Gemini Powered           ║")
#     print("╚══════════════════════════════════════════════╝")
#     print(f"{C.END}")

#     # ---- Check API Key ----
#     if not GEMINI_API_KEY:
#         print(f"{C.RED}❌ GEMINI_API_KEY not set!")
#         print(f"   Create a .env file with: GEMINI_API_KEY=your_key_here")
#         print(f"   Get your key at: https://aistudio.google.com/apikey{C.END}")
#         sys.exit(1)

#     # ---- Initialize Gemini ----
#     from google import genai
#     client = genai.Client(api_key=GEMINI_API_KEY)
#     print(f"  {C.GREEN}✅ Gemini connected{C.END}")

#     # ---- Get Goal ----
#     print(f"\n{C.BOLD}Enter your startup goal:{C.END}")
#     goal = input(f"{C.CYAN}  > {C.END}").strip()

#     if not goal:
#         print(f"{C.RED}  No goal entered. Exiting.{C.END}")
#         sys.exit(0)

#     print(f"\n  Goal: {C.BOLD}{goal}{C.END}")
#     print(f"  Starting pipeline...\n")

#     # ---- Pipeline ----
#     all_research = ""
#     all_documents = {}
#     max_replans = 2
#     extra_context = ""

#     for round_num in range(max_replans + 1):
#         if round_num > 0:
#             print(f"\n{C.YELLOW}{'='*60}")
#             print(f"  REPLAN ROUND {round_num}")
#             print(f"{'='*60}{C.END}")

#         # Step 1: Planner
#         plan = planner_agent(client, goal, extra_context)

#         # Step 2: Executor
#         research, documents = executor_agent(client, goal, plan)
#         all_research += research
#         all_documents.update(documents)

#         # Step 3: Decision
#         decision = decision_agent(client, goal, all_research, all_documents)

#         if decision.get("approved", True):
#             break
#         else:
#             gaps = decision.get("gaps", [])
#             extra_context = f"Previous research had gaps: {', '.join(gaps)}. Focus on filling these gaps."

#     # ---- Generate Final Strategy ----
#     strategy = generate_final_strategy(client, goal, all_research, decision)

#     # ---- Save Files ----
#     print(f"\n{C.BOLD}{C.GREEN}{'='*60}")
#     print(f"  SAVING RESULTS")
#     print(f"{'='*60}{C.END}")

#     saved = []

#     # Save strategy
#     path = save_file("strategy.md", strategy)
#     saved.append(("Strategy", path))
#     print(f"  📄 Strategy saved: {path}")

#     # Save documents
#     for doc_type, content in all_documents.items():
#         filename = f"{doc_type}.md"
#         path = save_file(filename, content)
#         saved.append((doc_type.replace("_", " ").title(), path))
#         print(f"  📄 {doc_type} saved: {path}")

#     # ---- Summary ----
#     confidence = decision.get("confidence", 0.7)
#     conf_bar = "█" * int(confidence * 20) + "░" * (20 - int(confidence * 20))

#     print(f"\n{C.BOLD}{C.CYAN}{'='*60}")
#     print(f"  ✅ DONE!")
#     print(f"{'='*60}{C.END}")
#     print(f"\n  Goal: {goal}")
#     print(f"  Confidence: [{conf_bar}] {confidence:.0%}")
#     print(f"  Files saved to: {OUTPUT_DIR}")
#     print(f"  Documents: {len(saved)}")

#     for name, path in saved:
#         print(f"    📄 {name}: {os.path.basename(path)}")

#     if decision.get("strengths"):
#         print(f"\n  {C.GREEN}Key Strengths:{C.END}")
#         for s in decision["strengths"][:3]:
#             print(f"    ✅ {s}")

#     if decision.get("risks"):
#         print(f"\n  {C.YELLOW}Key Risks:{C.END}")
#         for r in decision["risks"][:3]:
#             print(f"    ⚠️  {r}")

#     print(f"\n  {C.BOLD}Open output/ folder to view your documents!{C.END}\n")


# if __name__ == "__main__":
#     main()
