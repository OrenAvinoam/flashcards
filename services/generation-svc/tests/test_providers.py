"""Unit tests for generation-svc — no real LLM calls."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from generation_svc.providers import CardDraft, OllamaProvider
from generation_svc.worker import extract_text_from_pdf


@pytest.mark.asyncio
async def test_ollama_provider_parses_response() -> None:
    drafts = [{"front": "Q1", "back": "A1"}, {"front": "Q2", "back": "A2"}]
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": json.dumps(drafts)}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        provider = OllamaProvider("http://localhost:11434", "llama3.2")
        result = await provider.generate_cards("Some text", count=2)

    assert len(result) == 2
    assert isinstance(result[0], CardDraft)
    assert result[0].front == "Q1"


def test_extract_text_from_pdf_empty_bytes() -> None:
    import io
    import pypdf

    # Create a minimal valid PDF in memory
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    text = extract_text_from_pdf(pdf_bytes)
    assert isinstance(text, str)
