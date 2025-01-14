FROM python:3.11

ENV PYTHONUNBUFFERED 1
WORKDIR /app

ADD . .

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8080"]

EXPOSE 8080
# 