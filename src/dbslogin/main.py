import logging
import re
from base64 import urlsafe_b64decode

from dbslogin.gmail import Gmail, Message

logger = logging.getLogger(__name__)


def main():
    """
    Entrypoint for Cloud Run function that checks for a OTP email message
    """
    logger.info("Beginning bank statement extraction")
    client = Gmail()
    messages: list[Message] = client.get_emails()

    for message in messages:
        for part in message.parts:
            byte_data = client.search_data_key(part.data)
            data = urlsafe_b64decode(byte_data).decode("utf-8")

            if not data:
                continue

            if match := re.search(r"\d{6}", data):
                otp = match.group(0)
                print(otp)
                break


if __name__ == "__main__":
    main()
