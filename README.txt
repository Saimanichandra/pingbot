# SiteCareGuard - Local Setup Guide

## 1️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate  (on Windows)
source venv/bin/activate (on macOS/Linux)

## 2️⃣ Install Dependencies
pip install -r requirements.txt

## 3️⃣ Run Migrations
python manage.py migrate

## 4️⃣ Start Server
python manage.py runserver

Then open your browser and go to:
http://127.0.0.1:8000/

---
Redis + Celery setup :
redis-server
celery -A website_monitor worker --loglevel=info --pool=solo
 celery -A website_monitor beat --loglevel=info
