import streamlit as st
import requests
import uuid

API_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="AI Healthcare Assistant", layout="wide")


if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "waiting_for_location" not in st.session_state:
    st.session_state.waiting_for_location = False

if "hospitals" not in st.session_state:
    st.session_state.hospitals = []

st.title("🏥 AI Healthcare Assistant")

col1, col2 = st.columns([6,1])

with col2:
    if st.button("🗑 Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.waiting_for_location = False
        st.session_state.hospitals = []
        st.rerun()

for role, msg in st.session_state.chat_history:
    if role == "You":
        st.markdown(f"**🧑 You:** {msg}")
    else:
        st.markdown(f"**🤖 AI:** {msg}")

st.divider()

user_input = st.chat_input("Type your message...")

if user_input:
    response = requests.post(
        API_URL,
        json={
            "query": user_input,
            "session_id": st.session_state.session_id
        }
    )

    data = response.json()
    reply = data.get("response")

    st.session_state.chat_history.append(("You", user_input))
    st.session_state.chat_history.append(("AI", reply))
    if "provide your location" in reply.lower():
        st.session_state.waiting_for_location = True

    st.rerun()

if st.session_state.waiting_for_location:
    location = st.text_input("📍 Enter your location")

    if st.button("Submit Location"):

        response = requests.post(
            API_URL,
            json={
                "query": location,
                "location": location,
                "session_id": st.session_state.session_id
            }
        )

        data = response.json()
        reply = data.get("response")

        st.session_state.chat_history.append(("You", location))
        st.session_state.chat_history.append(("AI", reply))

        st.session_state.waiting_for_location = False
        st.rerun()
def display_hospitals(hospitals):

    st.subheader("🏥 Nearby Hospitals")

    for hospital in hospitals:

        col1, col2 = st.columns([1,2])

        with col1:
            if hospital.get("image"):
                st.image(hospital["image"], use_container_width=True)

        with col2:
            st.markdown(f"### {hospital.get('name')}")
            st.write(f"⭐ Rating: {hospital.get('rating')}")
            st.write(f"📍 Address: {hospital.get('address')}")
            st.write(f"📏 Distance: {hospital.get('distance')}")
            st.write(f"🕒 Open 24/7: {hospital.get('open_24_7')}")

            if hospital.get("map_link"):
                st.markdown(f"[🗺 View on Map]({hospital['map_link']})")

        st.divider()