import streamlit as st
import requests
import time

BACKEND = "http://127.0.0.1:8000"

st.set_page_config(page_title="Founder AI", layout="wide")

st.title("🚀 Founder AI – Startup Strategy Builder")

goal = st.text_area("Enter your startup idea")
context = st.text_area("Additional context (optional)")

if st.button("Generate Strategy"):

    if not goal:
        st.warning("Please enter a startup idea.")
        st.stop()

    with st.spinner("Starting analysis..."):
        res = requests.post(
            f"{BACKEND}/api/start",
            json={"goal": goal, "context": context},
        )

        task_id = res.json()["task_id"]

    progress = st.progress(0)

    while True:
        status_res = requests.get(f"{BACKEND}/api/status/{task_id}")
        data = status_res.json()

        if data["status"] == "running":
            progress.progress(40)
            time.sleep(2)

        elif data["status"] == "completed":
            progress.progress(100)

            st.success("Strategy Generated Successfully!")

            st.subheader("📋 Research Plan")
            st.json(data["plan"])

            st.subheader("📄 Documents")
            for name, doc in data["documents"].items():
                with st.expander(name):
                    st.markdown(doc)

            st.subheader("🧠 Decision")
            st.json(data["decision"])

            st.subheader("🏆 Final Strategy")
            st.markdown(data["final_strategy"])

            break

        elif data["status"] == "error":
            st.error(data["error"])
            break

        time.sleep(2)