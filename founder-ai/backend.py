import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from google import genai
import uuid

from agents import (
    planner_agent,
    executor_agent,
    decision_agent,
    generate_final_strategy,
)

app = FastAPI()

client = genai.Client(api_key="")

tasks = {}

class StartRequest(BaseModel):
    goal: str
    context: str | None = ""


@app.post("/api/start")
async def start_task(req: StartRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {"status": "running"}

    background_tasks.add_task(run_pipeline, task_id, req.goal, req.context)

    return {"task_id": task_id}

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    return tasks.get(task_id, {"error": "Invalid task id"})

def run_pipeline(task_id, goal, context):
    try:
        raw_plan = planner_agent(client, goal, context)
        if isinstance(raw_plan, list):
            clean_plan = "\n".join(
                [f"- {step.get('description', '')}" for step in raw_plan]
            )
        else:
            clean_plan = str(raw_plan)
        research, documents = executor_agent(client, goal, raw_plan)
        decision = decision_agent(client, goal, research, documents)

        final_strategy = generate_final_strategy(
            client, goal, research, decision
        )

        tasks[task_id] = {
            "status": "completed",
            "documents": documents,
            "decision": decision,
            "final_strategy": final_strategy,
        }

    except Exception as e:
        tasks[task_id] = {
            "status": "error",
            "error": str(e),
        }