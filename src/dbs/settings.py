from pydantic_settings import BaseSettings, SettingsConfigDict


class CloudSettings(BaseSettings):
    dbs_user_id: str = ""
    dbs_pin: str = ""
    project_id: str = ""
    secret_id: str = ""
    trusted_user_emails: list = []
    otp_email_subject: str = ""
    bucket_name: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = CloudSettings()
