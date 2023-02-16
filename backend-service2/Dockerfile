FROM --platform=linux/x86_64 python:3.9

WORKDIR /app
COPY requirements.txt /app/

RUN python -m pip install -r requirements.txt

COPY . /app/

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
