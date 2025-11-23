from twilio.rest import Client
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_sms(to_number: str, message: str) -> bool:
    try:
        sid = settings.TWILIO_ACCOUNT_SID
        token = settings.TWILIO_AUTH_TOKEN
        from_num = settings.TWILIO_FROM_NUMBER

        if not sid or not token or not from_num:
            logger.error("❌ Missing Twilio credentials in settings.py")
            return False

        client = Client(sid, token)
        sms = client.messages.create(
            body=message,
            from_=from_num,
            to=to_number
        )

        logger.info(f"📩 SMS sent to {to_number}, SID: {sms.sid}")
        return True

    except Exception as e:
        logger.error(f"❌ SMS sending FAILED: {e}")
        return False
