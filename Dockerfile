FROM python:3.10

WORKDIR /app
COPY . .
ENV PYTHONPATH=/app

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "dtlabs.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
