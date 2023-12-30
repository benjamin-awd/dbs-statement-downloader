from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from dbslogin.gmail.credentials import get_gmail_service
from dbslogin.settings import cloud_settings

if TYPE_CHECKING:
    from googleapiclient._apis.gmail.v1.resources import GmailResource

logger = logging.getLogger(__name__)


class Gmail:
    def __init__(self, gmail_service: Optional[GmailResource] = None):
        if not gmail_service:
            self.gmail_service = get_gmail_service()

    def get_emails(self, query="is:unread", latest=False) -> list[Message]:
        if subject := cloud_settings.otp_email_subject:
            query += " " + subject

        emails = (
            self.gmail_service.users()
            .messages()
            .list(userId="me", q=query)
            .execute()
            .get("messages")
        )

        if not emails:
            logger.info("No emails found using query: '%s'", query)
            sys.exit(0)

        if latest:
            emails = [emails[0]]

        messages = []
        for email in emails:
            email_id = email["id"]
            logger.info("Retrieving email %s", email_id)
            message = (
                self.gmail_service.users()
                .messages()
                .get(userId="me", id=email_id)
                .execute()
            )
            messages.append(message)

        return [
            Message(message, self.gmail_service) for message in messages  # type: ignore
        ]

    def search_data_key(self, part: dict):
        """Recursively searches message part for a 'data' key"""
        for key, value in part.items():
            if key == "data":
                return value
            if isinstance(value, dict):
                result = self.search_data_key(value)
                if result is not None:
                    return result
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        result = self.search_data_key(item)
                        if result is not None:
                            return result
        return None


class Message(Gmail):
    def __init__(self, data: dict, gmail_service: GmailResource):
        self.message_id: str = data.get("id")  # type: ignore
        self.payload: dict = data.get("payload")  # type: ignore
        self.gmail_service = gmail_service
        self.trusted_user_emails = cloud_settings.trusted_user_emails
        super().__init__(gmail_service)

    def mark_as_read(self):
        logger.info("Marking email %s as read", self.message_id)
        return (
            self.gmail_service.users()
            .messages()
            .modify(
                userId="me", id=self.message_id, body={"removeLabelIds": ["UNREAD"]}
            )
            .execute()
        )

    @property
    def subject(self) -> str:
        for item in self.payload["headers"]:
            if item["name"] == "Subject":
                return item["value"]
        raise RuntimeError("Subject could not be found")

    @property
    def parts(self) -> list[MessagePart] | None:
        """Return parts and nested parts"""
        if parts := self.payload.get("parts"):
            nested_parts = [
                nested_part
                for part in list(parts)
                if part.get("parts")
                for nested_part in part.get("parts")
            ]
            return [MessagePart(part) for part in parts + nested_parts]

        return None

    @property
    def from_trusted_user(self) -> bool:
        """Check if user is trusted"""
        for item in self.payload["headers"]:
            if item["name"] == "From":
                for trusted_email in self.trusted_user_emails:
                    if f"<{trusted_email}>" in item["value"]:
                        return True

        logger.info("No trusted user found")
        return False


@dataclass
class MessagePart:
    def __init__(self, data: dict):
        self.data = data
        self.part_id: str | None = data.get("partId")
        self.filename: str | None = data.get("filename")
        self.body: dict | None = data.get("body")

    def __repr__(self):
        return str(self.data)
