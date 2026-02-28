import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from pydantic import Field, BaseModel
from typing import List
from recommend import get_nearest_hospitals, get_speciality_hospitals
import json

API_key = os.getenv('GOOGLE_API_KEY')
llm_model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', google_api_key=API_key)

class BestHospitalFet(BaseModel):
    name: str = Field(description='Hospital name')
    rating: float = Field(description='Hospital rating')
    address: str = Field(description='Hospital address')
    url: str = Field(description='Provide me the url of the hospital')
    explanation: str = Field(description='Why it is good')


class BestHospitalList(BaseModel):
    hospitals: List[BestHospitalFet]


class BestSpecialityHospital(BaseModel):
    name: str = Field(description='Provide here the hospital name')
    rating: float = Field(description='Provide Hospital Rating')
    address: str = Field(description='Provide Hospital address')
    url: str = Field(description='Provide the hospital url')
    photo_url: str = Field(description='Provide hospital photo url')
    explanation: str = Field(description='Why it is good')

class BestSpecialityHospitalList(BaseModel):
    hospitals: List[BestSpecialityHospital]

@tool
def best_hospital(query: str) ->BestHospitalList:
    """
    Returns the best nearby hospitals based on user location.

    Args:
        query (str): Location or search query.

    Returns:
        BestHospitalList: Structured list of hospitals with rating and explanation.
    """
    
    
    try:
        hospital_data = get_nearest_hospitals(query)

        filter_rating = []
        for ratg in hospital_data:
            rating = ratg.get('rating', None)
            try:
                rating = float(rating)
            except (TypeError, ValueError):
                rating = 0.0 
           
            filter_rating.append({
                "name": ratg.get('name'),
                "rating": rating if rating>0 else None,
                "address": ratg.get('address'),
                "url": ratg.get('url')
            })
            
        best_hospital_template = PromptTemplate(
            input_variables=['query', 'filter_rating'],
            template='''You are an AI Assistant finding the best hospitals based on user query input.

User Query:
{query}

Available Hospitals:
{filter_rating}

Instructions:
1. For each hospital, provide:
    - name
    - rating
    - address
    - explaination (brief reason why it is good)
    - url (official website URL or Google Maps link; if unknown, use "N/A")
2. Return all hospitals in a structured list.
'''
        )

        hospital_data_text_rating = json.dumps(filter_rating, indent=2)
        prompt = best_hospital_template.format(
            query=query,
            filter_rating=hospital_data_text_rating
        )

        structure_llm_model_rating = llm_model.with_structured_output(BestHospitalList)
        response = structure_llm_model_rating.invoke(prompt)
        return response

           
    except Exception as e:
        print(f"Error for getting the best hospital: {e}")

@tool
def speciality_hospital(query:str, speciality:str):
    """
    Returns top speciality hospitals based on location and medical field.

    Args:
        query (str): User location.
        speciality (str): Required medical speciality.

    Returns:
        BestSpecialityHospitalList: Structured list of speciality hospitals.
    """
    try:
        speciality_hospital_data = get_speciality_hospitals(query, speciality)

        filter_rating = []
        for data in speciality_hospital_data:
            ratings = data.get('rating', None)
            try:
                ratings = float(ratings)
            except (TypeError, ValueError):
                ratings = 0.0

            filter_rating.append(
                {
                    "name": data.get('name'),
                    "rating": ratings if ratings > 0 else None,
                    "address": data.get("address"),
                    "url": data.get("url")
                }
            )

        speciality_template = PromptTemplate(
            input_variables=['query', 'speciality', 'hospital_data'],
            template='''You are an AI assistant finding the best speciality hospitals based on user input.

User Query:
{query}

Speciality:
{speciality}

Hospital Data:
{hospital_data}

Instructions:
1. Provide the top hospitals (up to 5) for the given speciality.
2. For each, include name, rating, address, url, explanation (brief reasons: services, labs, doctors, infrastructure).
3. Return the result as a structured list.
'''
        )

        speciality_data = json.dumps(filter_rating, indent=2)
        prompt = speciality_template.format(
            query=query,
            speciality=speciality,
            hospital_data=speciality_data
        )

        structured_output_speciality = llm_model.with_structured_output(BestSpecialityHospitalList)
        result = structured_output_speciality.invoke(prompt)
        return result
    
    except Exception as e:
        return f"Error getting the speciality hospital, {e}"




