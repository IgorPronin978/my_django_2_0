FROM python:3.12-slim

WORKDIR /app

# Системные пакеты
 RUN apt-get update && apt-get install -y \
         netcat-openbsd gcc libpq-dev && apt-get clean

# Python-зависимости
 COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Скрипты
 COPY entrypoint.sh wait-for-db.sh ./
 RUN chmod +x entrypoint.sh wait-for-db.sh

# --- переменная окружения для этапа build ---
 ENV DOCKERIZED=1 \
     PYTHONUNBUFFERED=1 \
     PYTHONDONTWRITEBYTECODE=1

# Код проекта
 COPY . .

 # collectstatic -> /static  (путь выбирается по DOCKERIZED=1)
 RUN mkdir -p /static && python manage.py collectstatic --no-input

 ENTRYPOINT ["./entrypoint.sh"]