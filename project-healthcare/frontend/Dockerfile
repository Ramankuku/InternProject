FROM python:3.9-slim

WORKDIR /app

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY frontend/ ./frontend
EXPOSE 8501

CMD ["streamlit", "run","frontend/stream.py" ,"--server.address=0.0.0.0", "--server.port=8501"]


