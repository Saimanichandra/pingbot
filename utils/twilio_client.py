from twilio.rest import Client
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_sms(to_number: str, message: str) -> bool:
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_FROM_NUMBER,
            to=to_number
        )
        logger.info(f"SMS sent to {to_number} — SID:{msg.sid}")
        return True
    except Exception as e:
        logger.error(f"SMS FAILED to {to_number}: {e}")
        return False
