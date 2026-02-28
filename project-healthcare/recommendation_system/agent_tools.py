from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from .hospital_recommend import speciality_hospital, best_hospital
from .user_symptoms import user_symptom
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
llm_model = ChatOpenAI(model='gpt-4o-mini', api_key=API_KEY)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=API_KEY
)

tools = [speciality_hospital, best_hospital, user_symptom]

agent = create_react_agent(llm, tools)

