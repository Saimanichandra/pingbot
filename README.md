...content from GitHub...
>>>>>>> origin/main
# 🌐 SiteCareGuard – Website Health Monitor (Email + SMS Alerts)

This Django project monitors website uptime and sends **Email and Twilio SMS alerts** when a site is **down for more than 2 minutes**, then notifies again when it recovers.

---

## 🚀 Features
- Periodic health checks (via `django-crontab`, every 1 minute)
- Alerts via **Email** and **Twilio SMS**
- Auto-seeded demo sites (`Google`, `Example`, `InvalidSite`)
-  Celery
- Redis

---

## 🧩 Installation

```bash
git clone <this repo> SiteCareGuard
cd SiteCareGuard
pip install -r requirements.txt
```

If you are using a virtual environment:
```bash
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
```

---

## ⚙️ Environment Configuration

Create a file named `.env` in your project root (or copy from `.env.example`):

```bash
cp .env.example .env
```

Then fill in your credentials:

```
# Twilio (for SMS alerts)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
TWILIO_FROM_NUMBER=+1234567890

# Email (for email alerts)
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587

# Django secret key if needed
SECRET_KEY=django-insecure-xxxxxx
```

⚠️ **For Gmail**: enable [App Passwords](https://myaccount.google.com/apppasswords) — do **not** use your real password.

---

## 🧰 Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🧪 Seed Demo Websites

Add sample websites (2 working, 1 broken):

```bash
python manage.py seed_test_sites
```

Then open Django Admin or run a manual check:

```bash
python manage.py check_websites
```

If “InvalidSite” stays down for 2+ minutes, you’ll get **both an Email and SMS alert**.

---

## ⏱️ Automatic Monitoring (Cron)

The project uses `django-crontab` to schedule checks every minute:

```bash
python manage.py crontab add
python manage.py crontab show   # verify it’s listed
```

To remove:
```bash
python manage.py crontab remove
```

---

## 🧭 Admin Access (optional)
You can manage websites in the Django admin.

```bash
python manage.py createsuperuser
python manage.py runserver
```
Then visit: http://127.0.0.1:8000/admin/

---

## 🩺 Logs and Debugging

- Cron logs are typically in system logs (`/var/log/syslog` on Linux, or Task Scheduler on Windows).
- All alerts also log through Django’s `logging` system.
- To test SMS, ensure your Twilio number and recipient are verified (for trial accounts).

---

## 🧹 Cleanup / Stop
```bash
python manage.py crontab remove
deactivate  # if using virtual env
```

---

## 🛠️ Requirements
```
Django >= 5.x
twilio >= 8.0.0
django-crontab >= 0.8.0
requests
```

---

## 🧑‍💻 Author
**Sai Mani**  
A simple, production-ready website monitoring tool built in Django.
=======
# AIORI-2-HACKATHON-PROJECTS
This repository will contain the code and resources for the AIORI-2 hackathon that will be developed during the AIORI-2
>>>>>>> a68ab50d5ebd8e37133e61f775240cdc823818cf
