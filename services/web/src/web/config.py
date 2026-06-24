from flashcards_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "web"
    auth_svc_url: str = "http://auth-svc:8001"
    web_deck_svc_url: str = "http://deck-svc:8002"
    web_scheduler_svc_url: str = "http://scheduler-svc:8003"
    web_generation_svc_url: str = "http://generation-svc:8004"
    session_secret: str
    port: int = 8000


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
