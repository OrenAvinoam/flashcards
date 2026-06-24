from flashcards_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "auth-svc"
    auth_database_url: str
    port: int = 8001


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
