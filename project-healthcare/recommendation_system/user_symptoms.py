import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.tools import tool
from pydantic import Field, BaseModel
import pandas as pd 
from .hospital_recommend import best_hospital
from recommend import get_nearest_hospitals
from langchain_community.vectorstores import FAISS
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")


llm_model = ChatOpenAI(model='gpt-4o-mini', api_key=API_KEY)

class SymptomResponse(BaseModel):
    reason: str = Field(description='Provide the reason why happens')
    recommendation: str = Field(description='Provide the recommendations')
    emergency:bool= Field(description='Provide whether it is emergency or not')
    explaination: str = Field(description='Provide the explaination')

embeddings_doc = OpenAIEmbeddings(
    api_key=API_KEY,
    model="text-embedding-3-small"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

File_Path = os.path.join(
    BASE_DIR,
    "medical_rag_dataset_160_conditions.csv"
)
def read_csv_file(file_path):
    df =pd.read_csv(file_path)
    df['emergency'] = df['emergency'].astype(str).str.lower()
    df['severity'] = df['severity'].astype(str).str.lower()

    document = []

    for _, row in df.iterrows():
        symptoms = row['symptoms'].lower()
        symptoms = row['symptoms'].split(',')
        symptoms = ''.join(symptoms)
        

        content = f"""
Disease: {row['disease']}
category: {row['category']}
symptoms: {row['symptoms']}
emergency: {row['emergency']}
recommended_action: {row['recommended_action']}
"""
        doc = Document(
            page_content=content,
            metadata={
                "Disease": row['disease'],
                "body_location": row['body_location'],
                "category": row['category'],
                "severity":row["severity"]
            }
        )
        document.append(doc)

    return document

def create_store(file_path):
    create_document_data = read_csv_file(file_path)
    vector_store = FAISS.from_documents(create_document_data, embeddings_doc)
    retreiver = vector_store.as_retriever(search_kwargs={"k":3})
    return retreiver

retreiver = create_store(File_Path)


@tool
def user_symptom(query: str, location: Optional[str] = None):
    """
    Analyze symptoms using RAG and structured medical dataset.
    """

    try:
        if not query:
            return {
                "analysis": {},
                "hospitals": [],
                "emergency": False,
                "needs_location": False,
                "message": "Please enter symptoms."
            }

        docs = retreiver.invoke(query)

        emergency_flag = False
        for doc in docs:
            if doc.page_content.lower().find("emergency: yes") != -1:
                emergency_flag = True

        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = f"""
You are an AI medical assistant.

User Symptoms:
{query}

Context:
{context}

Instructions:
1. Explain reason clearly.
2. Give recommendation.
3. Provide short explanation.
Use simple language.
Do NOT decide emergency — it is pre-determined.
"""

        structured_llm = llm_model.with_structured_output(SymptomResponse)
        response = structured_llm.invoke(prompt)

        result = {
            "analysis": {
                "reason": response.reason,
                "recommendation": response.recommendation,
                "explaination": response.explaination
            },
            "hospitals": [],
            "emergency": emergency_flag,
            "needs_location": emergency_flag and not location,
            "message": None
        }

        # 🚨 Emergency Handling
        if emergency_flag:
            if location:
                hospitals = get_nearest_hospitals(location)

                if isinstance(hospitals, list):
                    result["hospitals"] = hospitals
                    result["message"] = "Emergency detected. Showing nearest hospitals."
                else:
                    result["message"] = str(hospitals)
            else:
                result["message"] = "Emergency detected. Please provide your location."

        return result

    except Exception as e:
        return {
            "analysis": {},
            "hospitals": [],
            "emergency": False,
            "needs_location": False,
            "message": f"Error: {str(e)}"
        }