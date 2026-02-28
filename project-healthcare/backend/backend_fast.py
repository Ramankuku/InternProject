from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import uuid

from recommendation_system.agent_tools import agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    location: Optional[str] = None
    session_id: str

chat_sessions = {}

@app.post("/chat")
def chat(request: ChatRequest):

    if request.session_id not in chat_sessions:
        chat_sessions[request.session_id] = []

    # Build input
    user_input = request.query

    if request.location:
        user_input += f"\nMy location is {request.location}"

    # Append user message
    chat_sessions[request.session_id].append(("user", user_input))

    response = agent.invoke({
        "messages": chat_sessions[request.session_id]
    })

    final_message = response["messages"][-1].content

    # Save assistant reply
    chat_sessions[request.session_id].append(
        ("assistant", final_message)
    )

    return {
        "response": final_message
    }