from google import genai 
import json
from tools import web_search, calculate, financial_formula, generate_document
client = genai.Client(api_key='')

class C:
    """ANSI color codes for terminal output."""
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def _log(callback, msg):
    """Send message to callback (for web UI) and always print to terminal."""
    for code in [C.BLUE, C.GREEN, C.YELLOW, C.RED, C.CYAN, C.BOLD, C.END]:
        clean = clean.replace(code, "")
    if callback:
        callback(clean.strip())
    print(msg)

def planner_agent(client, goal, extra_context="", log=None):
    """
    Analyzes the goal and creates a step-by-step research plan.
    Returns: list of dicts [{description, tool, tool_input}]
    """
    _log(log, f"\n{C.BOLD}{C.BLUE}{'='*60}\n  PLANNER AGENT\n{'='*60}{C.END}")

    prompt = f"""You are a startup planning expert. Create a research plan for this startup idea.

GOAL: {goal}
{f"ADDITIONAL CONTEXT: {extra_context}" if extra_context else ""}

Available tools:
- web_search: Search the internet (provide a search query)
- calculator: Do math or financial formulas (ltv, cac, burn_rate, runway, break_even, roi, mrr, arr)
- doc_generator: Generate documents (business_plan, pitch_deck, roadmap)

Create 6-10 steps. Steps should cover:
1. Market research (2-3 web searches)
2. Competitor analysis (1-2 web searches)
3. Financial calculations (1-2 calculator steps)
4. Document generation (business_plan, pitch_deck, roadmap)

Return a JSON array where each item has:
- "description": what this step does
- "tool": one of "web_search", "calculator", "doc_generator"
- "tool_input": the query/expression/doc_type to use

Example:
[
  {{"description": "Research market size", "tool": "web_search", "tool_input": "AI healthcare market size 2024"}},
  {{"description": "Calculate runway", "tool": "calculator", "tool_input": {{"formula": "runway", "params": {{"cash_balance": 500000, "monthly_burn": 50000}}}}}},
  {{"description": "Generate business plan", "tool": "doc_generator", "tool_input": "business_plan"}}
]"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.4,
                "max_output_tokens": 4096,
            },
        )

        plan = json.loads(response.text.strip())
        if isinstance(plan, dict):
            plan = plan.get("steps", plan.get("plan", []))

        _log(log, f"\n{C.CYAN}  Plan created with {len(plan)} steps:{C.END}")
        for i, step in enumerate(plan, 1):
            tool_icon = {"web_search": "🔍", "calculator": "🧮", "doc_generator": "📄"}.get(step.get("tool", ""), "❓")
            _log(log, f"    {i}. {tool_icon} {step.get('description', 'Step')}")

        return plan

    except Exception as e:
        _log(log, f"{C.RED}  Planner failed: {e}{C.END}")
        return [
            {"description": f"Research {goal}", "tool": "web_search", "tool_input": goal},
            {"description": "Research market size", "tool": "web_search", "tool_input": f"{goal} market size"},
            {"description": "Research competitors", "tool": "web_search", "tool_input": f"{goal} competitors"},
            {"description": "Generate business plan", "tool": "doc_generator", "tool_input": "business_plan"},
            {"description": "Generate pitch deck", "tool": "doc_generator", "tool_input": "pitch_deck"},
            {"description": "Generate roadmap", "tool": "doc_generator", "tool_input": "roadmap"},
        ]

def executor_agent(client, goal, plan, log=None):
    """
    Executes each plan step by calling the right tool.
    Returns: (research_text, documents_dict)
    """
    _log(log, f"\n{C.BOLD}{C.GREEN}{'='*60}\n  EXECUTOR AGENT\n{'='*60}{C.END}")

    research = ""
    documents = {}
    total = len(plan)

    for i, step in enumerate(plan, 1):
        desc = step.get("description", f"Step {i}")
        tool = step.get("tool", "web_search")
        tool_input = step.get("tool_input", "")

        _log(log, f"\n{C.YELLOW}  [{i}/{total}] {desc}{C.END}")

        try:
            if tool == "web_search":
                query = tool_input if isinstance(tool_input, str) else str(tool_input)
                result = web_search(query)
                research += f"\n\n--- Research: {desc} ---\n{result}"
                _log(log, f"Found results for: {query[:50]}...")

            elif tool == "calculator":
                if isinstance(tool_input, dict):
                    formula_name = tool_input.get("formula", "")
                    params = tool_input.get("params", {})
                    result = financial_formula(formula_name, params)
                elif isinstance(tool_input, str):
                    try:
                        parsed = json.loads(tool_input)
                        if isinstance(parsed, dict) and "formula" in parsed:
                            result = financial_formula(parsed["formula"], parsed.get("params", {}))
                        else:
                            result = calculate(tool_input)
                    except (json.JSONDecodeError, TypeError):
                        result = calculate(tool_input)
                else:
                    result = calculate(str(tool_input))

                research += f"\n\n--- Calculation: {desc} ---\n{result}"
                _log(log, f"  ✅ {result}")

            elif tool == "doc_generator":
                doc_type = tool_input if isinstance(tool_input, str) else str(tool_input)
                doc_type = doc_type.lower().strip()
                if "pitch" in doc_type:
                    doc_type = "pitch_deck"
                elif "road" in doc_type:
                    doc_type = "roadmap"
                elif "business" in doc_type or "plan" in doc_type:
                    doc_type = "business_plan"

                _log(log, f"  ⏳ Generating {doc_type}...")
                doc = generate_document(client, doc_type, goal, research)
                documents[doc_type] = doc
                _log(log, f"  ✅ Generated {doc_type} ({len(doc)} chars)")

            else:
                _log(log, f"  ⚠️ Unknown tool: {tool}")

        except Exception as e:
            _log(log, f"  ❌ Failed: {e}")

    return research, documents

def decision_agent(client, goal, research, documents, log=None):
    """
    Reviews everything and decides: approve or replan.
    Returns: dict {approved, confidence, strategy, gaps, strengths, risks}
    """
    _log(log, f"\n{C.BOLD}{C.CYAN}{'='*60}\n  DECISION AGENT\n{'='*60}{C.END}")

    docs_summary = ", ".join(f"{k} ({len(v)} chars)" for k, v in documents.items()) if documents else "None"

    prompt = f"""You are a senior startup strategy reviewer. Review the research results and decide if the strategy is ready.

STARTUP GOAL: {goal}

RESEARCH COLLECTED:
{research[-4000:] if len(research) > 4000 else research}

DOCUMENTS GENERATED: {docs_summary}

Review and respond with JSON:
{{
  "approved": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "why you made this decision",
  "strategy": "comprehensive strategy summary (500+ words if approved)",
  "gaps": ["list of gaps if not approved"],
  "strengths": ["key strengths found"],
  "risks": ["key risks identified"]
}}

If the research covers market, competitors, financials, and documents are generated - APPROVE.
Only REPLAN if critical information is clearly missing."""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.3,
                "max_output_tokens": 4096,
            },
        )

        decision = json.loads(response.text.strip())

        approved = decision.get("approved", True)
        confidence = decision.get("confidence", 0.7)

        status = "APPROVED ✅" if approved else "REPLAN 🔄"
        _log(log, f"\n  Decision: {status}")
        _log(log, f"  Confidence: {confidence:.0%}")

        if decision.get("strengths"):
            for s in decision["strengths"][:3]:
                _log(log, f"    ✅ {s}")

        if decision.get("risks"):
            for r in decision["risks"][:3]:
                _log(log, f"    ⚠️ {r}")

        if not approved and decision.get("gaps"):
            for g in decision["gaps"]:
                _log(log, f"    ❌ Gap: {g}")

        return decision

    except Exception as e:
        _log(log, f"  {C.RED}Decision agent error: {e}{C.END}")
        return {
            "approved": True,
            "confidence": 0.5,
            "strategy": "Strategy review encountered an error. Proceeding with available data.",
            "gaps": [],
            "strengths": [],
            "risks": [str(e)],
        }

def generate_final_strategy(client, goal, research, decision, log=None):
    """Generate the comprehensive final strategy document."""
    _log(log, f"\n{C.BOLD}  Generating final strategy...{C.END}")

    prompt = f"""You are a startup strategy expert. Create a comprehensive final strategy in Markdown.

STARTUP GOAL: {goal}

RESEARCH DATA:
{research[-5000:] if len(research) > 5000 else research}

KEY STRENGTHS: {json.dumps(decision.get('strengths', []))}
KEY RISKS: {json.dumps(decision.get('risks', []))}

Create a strategy document with:
# Startup Strategy: {goal}
## Executive Overview
## Market Opportunity
## Competitive Positioning
## Revenue Model & Unit Economics
## Go-to-Market Plan
## Key Metrics & KPIs to Track
## Risk Assessment & Mitigation
## Recommended Next Steps (prioritized)

Be specific, actionable, and data-driven."""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={"temperature": 0.5, "max_output_tokens": 8192},
        )
        return response.text.strip()
    except Exception as e:
        return decision.get("strategy", f"Strategy generation failed: {e}")
