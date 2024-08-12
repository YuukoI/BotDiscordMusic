FROM python:3.12

WORKDIR /app

COPY requirements.txt .
COPY . .

RUN apt-get update && apt-get install -y ffmpeg

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]