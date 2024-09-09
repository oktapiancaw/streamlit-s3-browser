FROM python:3.10.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .


ENTRYPOINT [ "streamlit", "run", "/app/src/main.py" , "--browser.gatherUsageStats", "false"]