from flashcards_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "scheduler-svc"
    redis_url: str = "redis://redis:6379"
    deck_svc_url: str = "http://deck-svc:8002"
    port: int = 8003


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
