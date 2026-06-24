import httpx


def make_http_client(base_url: str = "", timeout: float = 10.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(timeout),
        headers={"User-Agent": "flashcards-internal/1.0"},
    )
