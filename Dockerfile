FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py prober.py store.py ./
COPY static ./static

ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "python app.py"]
