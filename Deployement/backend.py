from fastapi import FastAPI
from pydantic import BaseModel
from database import init_db, get_user, add_user
import joblib
import numpy as np
import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

model = joblib.load(r"C:\Intern\Notebook\model.pkl")

RISK_LABELS = {
    0: "Low Risk",
    1: "Medium Risk",
    2: "Risky"
}

app = FastAPI()
init_db()

class User(BaseModel):
    user_id: str
    password: str

def predict_risk(user):
    features = np.array([[
        user["monthly_income"],
        user["num_active_bnpl_plans"],
        user["total_bnpl_amount"],
        user["average_emi"],
        user["bnpl_income_ratio"],
        user["Emi_delayed"]
    ]])

    risk = model.predict(features)[0]
    return risk

def get_explanation(user, risk_level):
    prompt = f"""
You are a BNPL Financial Health Assistant.

Facts:
- Active BNPL Plans: {user['num_active_bnpl_plans']}
- Average EMI: ₹{user['average_emi']}
- Income spent on EMI: {round(user['bnpl_income_ratio'] * 100)}%
- EMI Delayed: {user['Emi_delayed']}
- Risk Level: {RISK_LABELS[risk_level]}

Explain the user's financial health in simple language.
Provide what may happen next month if this continues.
If the user has no history of income and all it's a new user
Provide the new user Not to use the BNPL plans
Mention risks and give ONE precaution.
Explain in 30 words.
Each explanation starts on a new line.
"""

    response = gemini_model.generate_content(prompt)
    return response.text.strip()


@app.post("/signup")
def signup(user: User):
    if get_user(user.user_id):
        return {"status": "error", "message": "User already exists"}

    add_user(user.user_id, user.password)
    return {"status": "success", "message": "Signup successful"}

@app.post("/login")
def login(user: User):
    db_user = get_user(user.user_id)
    if db_user and db_user["password"] == user.password:
        return {"status": "success", "message": "Login successful"}
    return {"status": "error", "message": "Invalid credentials"}

@app.post("/logout")
def logout():
    return {"status": "success", "message": "Logged out"}

# ---------------- PAY ----------------
@app.post("/pay/{user_id}")
def risk_prediction(user_id: str):
    user = get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found"}

    for k in [
        "monthly_income",
        "num_active_bnpl_plans",
        "total_bnpl_amount",
        "average_emi",
        "bnpl_income_ratio",
        "Emi_delayed"
    ]:
        if user[k] is None:
            user[k] = 0

    risk = predict_risk(user)
    explanation = get_explanation(user, risk)

    if risk == 2:
        return {
            "status": "declined",
            "risk_level": "Risky",
            "explanation": explanation
        }

    return {
        "status": "success",
        "risk_level": RISK_LABELS[risk],
        "explanation": explanation
    }
