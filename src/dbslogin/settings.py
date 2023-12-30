from pydantic_settings import BaseSettings, SettingsConfigDict


class CloudSettings(BaseSettings):
    project_id: str = ""
    secret_id: str = ""
    trusted_user_emails: list = []
    otp_email_subject: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


cloud_settings = CloudSettings()
