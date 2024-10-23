FROM python:3.13
ENV PYTHONUNBUFFERED=1
WORKDIR /demo
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY src ./src
COPY main.py main.py
CMD ["uvicorn", "main:app", "--proxy-headers","--host", "0.0.0.0","--port", "80"]