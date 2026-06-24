from flashcards_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "deck-svc"
    deck_database_url: str
    port: int = 8002


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
