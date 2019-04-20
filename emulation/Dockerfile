# Client api image
FROM python:3.6-slim

EXPOSE 5000


WORKDIR .
ENV FLASK_APP app.py
COPY requirements.txt .
COPY app.py .
COPY emulation.py .
COPY settings.py .
COPY settings_docker.py .
COPY tokenization.py .

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "-m", "flask", "run", "--host", "0.0.0.0"]
