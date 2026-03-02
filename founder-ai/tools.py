"""
Tools - Simple functions for search, calculation, and document generation.
No classes, no complexity. Just functions that do one thing.
"""
import sys; from pathlib import Path; sys.path.append(str(Path(__file__).resolve().parent))
import ast
import math
import operator
import json
from google import genai
client = genai.Client(api_key="")

def web_search(query, max_results=5):
    """Search the web using DuckDuckGo. Returns formatted string."""
    try:
        from ddgs import DDGS
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"No results found for: {query}"

        lines = [f'Search: "{query}" ({len(results)} results)\n']
        for i, r in enumerate(results, 1):
            lines.append(f"  {i}. {r.get('title', 'No title')}")
            lines.append(f"     {r.get('body', r.get('snippet', ''))}")
            lines.append(f"     URL: {r.get('href', r.get('link', ''))}\n")

        return "\n".join(lines)

    except Exception as e:
        return f"Search error for '{query}': {e}"


# ===================== CALCULATOR =====================

# Safe operators for AST-based math eval
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
}


def _safe_eval(node):
    """Recursively evaluate an AST node (no eval() used)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    elif isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculate(expression):
    """Safely evaluate a math expression. Returns result string."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return f"{expression} = {result:,.2f}"
    except Exception as e:
        return f"Calculation error: {e}"


def financial_formula(name, params):
    """
    Calculate a startup financial formula.
    Supported: ltv, cac, burn_rate, runway, break_even, roi, mrr, arr
    """
    name = name.lower().strip()
    p = params

    try:
        if name == "ltv":
            r = p["avg_revenue"] * p["avg_lifespan"]
            return f"LTV = ${r:,.2f} (${p['avg_revenue']:,.0f}/period x {p['avg_lifespan']:.0f} periods)"

        elif name == "cac":
            r = p["total_marketing"] / p["new_customers"]
            return f"CAC = ${r:,.2f} (${p['total_marketing']:,.0f} / {p['new_customers']:.0f} customers)"

        elif name == "burn_rate":
            r = p["total_expenses"] / p["months"]
            return f"Burn Rate = ${r:,.2f}/month"

        elif name == "runway":
            r = p["cash_balance"] / p["monthly_burn"]
            return f"Runway = {r:.1f} months (${p['cash_balance']:,.0f} / ${p['monthly_burn']:,.0f}/mo)"

        elif name == "break_even":
            r = p["fixed_costs"] / (p["price"] - p["variable_cost"])
            return f"Break-Even = {r:,.0f} units"

        elif name == "roi":
            r = ((p["gain"] - p["cost"]) / p["cost"]) * 100
            return f"ROI = {r:.1f}%"

        elif name == "mrr":
            r = p["customers"] * p["avg_monthly_revenue"]
            return f"MRR = ${r:,.2f}/month"

        elif name == "arr":
            r = p["customers"] * p["avg_monthly_revenue"] * 12
            return f"ARR = ${r:,.2f}/year"

        else:
            return f"Unknown formula: {name}"

    except KeyError as e:
        return f"Missing parameter {e} for formula '{name}'"
    except ZeroDivisionError:
        return f"Division by zero in '{name}'"


# ===================== DOCUMENT GENERATOR =====================

def generate_document(client, doc_type, goal, research):
    """
    Use Gemini to generate a startup document.
    doc_type: 'business_plan', 'pitch_deck', or 'roadmap'
    Returns markdown string.
    """
    prompts = {
        "business_plan": f"""Create a detailed business plan in Markdown for this startup:

GOAL: {goal}

RESEARCH & DATA:
{research}

Include these sections:
# Business Plan
## Executive Summary
## Problem Statement
## Solution
## Target Market
## Market Size (TAM/SAM/SOM)
## Business Model & Revenue Streams
## Competitive Analysis
## Go-to-Market Strategy
## Team Requirements
## Financial Projections (Year 1-3)
## Funding Requirements
## Key Risks & Mitigations

Be specific with numbers and data from the research.""",

        "pitch_deck": f"""Create a 10-slide investor pitch deck in Markdown for this startup:

GOAL: {goal}

RESEARCH & DATA:
{research}

Format as slides:
# Pitch Deck
## Slide 1: The Problem
## Slide 2: Our Solution
## Slide 3: Market Opportunity
## Slide 4: How It Works
## Slide 5: Business Model
## Slide 6: Traction & Milestones
## Slide 7: Competition
## Slide 8: Go-to-Market Strategy
## Slide 9: Team
## Slide 10: The Ask (Funding)

Keep each slide concise with bullet points and bold metrics.""",

        "roadmap": f"""Create a product roadmap in Markdown for this startup:

GOAL: {goal}

RESEARCH & DATA:
{research}

Include these phases:
# Product Roadmap
## Phase 1: Foundation (Months 1-3)
## Phase 2: MVP Launch (Months 4-6)
## Phase 3: Growth (Months 7-12)
## Phase 4: Scale (Year 2)
## Key Milestones
## Resource Requirements

Be specific about features, deadlines, and success metrics.""",
    }

    prompt = prompts.get(doc_type)
    if not prompt:
        return f"Unknown document type: {doc_type}"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={"temperature": 0.6, "max_output_tokens": 8192},
        )
        return response.text.strip()
    except Exception as e:
        return f"Document generation failed: {e}"
