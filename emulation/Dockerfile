# Client api image
FROM python:3.6-slim

WORKDIR .

EXPOSE 5000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP app.py

COPY app.py .
COPY emulation.py .
COPY tokenization.py .
COPY settings.py .
COPY settings_docker.py .
COPY entrypoint.sh .

ENTRYPOINT ["./entrypoint.sh"]
CMD ["run"]
