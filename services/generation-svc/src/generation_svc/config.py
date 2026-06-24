from flashcards_common.settings import CommonSettings


class Settings(CommonSettings):
    service_name: str = "generation-svc"
    redis_url: str = "redis://redis:6379"
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    port: int = 8004

    def model_post_init(self, __context: object) -> None:
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY must be set when LLM_PROVIDER=gemini")


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
