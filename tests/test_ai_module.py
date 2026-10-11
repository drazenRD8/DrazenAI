"""
Testovi za DrazenAI — ai_module.
Pokreni: pytest -v
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import requests

# Dodaj root u path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_module import (
    proveri_vezu,
    lista_modela,
    pitaj,
    _pitaj_ceo,
    _pitaj_stream,
    ocisti_istoriju,
    sacuvaj_istoriju,
    broj_poruka,
    HISTORY,
    OLLAMA_URL,
    MODEL,
)


# ============================================================
# FIXTURE — čisti HISTORY pre svakog testa
# ============================================================

@pytest.fixture(autouse=True)
def clean_history():
    """Čisti istoriju pre i posle svakog testa."""
    HISTORY.clear()
    yield
    HISTORY.clear()


def make_mock_response(json_data, status_code=200):
    """Napravi mock response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


# ============================================================
# TESTIRANJE proveri_vezu()
# ============================================================

class TestProveriVezu:
    """Testovi za proveri_vezu funkciju."""

    @patch("ai_module.requests.get")
    def test_connection_ok(self, mock_get):
        """Testira uspešnu vezu."""
        mock_get.return_value = make_mock_response({
            "models": [{"name": "llama3.2:latest"}]
        })
        ok, msg = proveri_vezu()
        assert ok is True
        assert "OK" in msg

    @patch("ai_module.requests.get")
    def test_no_models(self, mock_get):
        """Testira kada nema modela."""
        mock_get.return_value = make_mock_response({"models": []})
        ok, msg = proveri_vezu()
        assert ok is False
        assert "Nema instaliranih modela" in msg

    @patch("ai_module.requests.get")
    def test_model_not_found(self, mock_get):
        """Testira kada model nije nađen."""
        mock_get.return_value = make_mock_response({
            "models": [{"name": "mistral:latest"}]
        })
        ok, msg = proveri_vezu()
        assert ok is False
        assert "nije nađen" in msg

    @patch("ai_module.requests.get")
    def test_connection_error(self, mock_get):
        """Testira ConnectionError."""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        ok, msg = proveri_vezu()
        assert ok is False
        assert "Ne mogu da se povežem" in msg

    @patch("ai_module.requests.get")
    def test_general_exception(self, mock_get):
        """Testira opštu grešku."""
        mock_get.side_effect = Exception("Test greška")
        ok, msg = proveri_vezu()
        assert ok is False
        assert "Greška" in msg


# ============================================================
# TESTIRANJE lista_modela()
# ============================================================

class TestListaModela:
    """Testovi za lista_modela funkciju."""

    @patch("ai_module.requests.get")
    def test_returns_models(self, mock_get):
        """Testira vraćanje liste modela."""
        mock_get.return_value = make_mock_response({
            "models": [
                {"name": "llama3.2:latest"},
                {"name": "mistral:latest"},
            ]
        })
        result = lista_modela()
        assert result == ["llama3.2:latest", "mistral:latest"]

    @patch("ai_module.requests.get")
    def test_empty_on_error(self, mock_get):
        """Testira praznu listu na grešku."""
        mock_get.side_effect = Exception("Error")
        assert lista_modela() == []


# ============================================================
# TESTIRANJE _pitaj_ceo()
# ============================================================

class TestPitajCeo:
    """Testovi za _pitaj_ceo funkciju."""

    @patch("ai_module.requests.post")
    def test_successful_response(self, mock_post):
        """Testira uspešan odgovor."""
        mock_post.return_value = make_mock_response({
            "message": {"content": "Odgovor AI-ja"}
        })
        payload = {"model": MODEL, "messages": []}
        result = _pitaj_ceo(payload)
        assert result == "Odgovor AI-ja"

    @patch("ai_module.requests.post")
    def test_stream_set_to_false(self, mock_post):
        """Testira da je stream postavljen na False."""
        mock_post.return_value = make_mock_response({
            "message": {"content": "Test"}
        })
        payload = {"model": MODEL, "messages": [], "stream": True}
        _pitaj_ceo(payload)
        assert payload["stream"] is False


# ============================================================
# TESTIRANJE pitaj()
# ============================================================

class TestPitaj:
    """Testovi za pitaj funkciju."""

    @patch("ai_module._pitaj_ceo")
    def test_pitaj_no_stream(self, mock_ceo):
        """Testira pitaj bez streaming-a."""
        mock_ceo.return_value = "Odgovor"
        result = pitaj("Zdravo", stream=False)
        assert result == "Odgovor"
        assert broj_poruka() == 2  # user + assistant

    @patch("ai_module._pitaj_ceo")
    def test_history_added(self, mock_ceo):
        """Testira da se istorija dodaje."""
        mock_ceo.return_value = "AI odgovor"
        pitaj("Pitanje", stream=False)
        assert len(HISTORY) == 2
        assert HISTORY[0]["role"] == "user"
        assert HISTORY[0]["content"] == "Pitanje"
        assert HISTORY[1]["role"] == "assistant"
        assert HISTORY[1]["content"] == "AI odgovor"

    @patch("ai_module.requests.post")
    def test_timeout_error(self, mock_post):
        """Testira timeout."""
        mock_post.side_effect = requests.exceptions.Timeout()
        result = pitaj("test", stream=False)
        assert "timeout" in result.lower()

    @patch("ai_module.requests.post")
    def test_connection_error(self, mock_post):
        """Testira connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        result = pitaj("test", stream=False)
        assert "Ne mogu da se povežem" in result


# ============================================================
# TESTIRANJE ocisti_istoriju()
# ============================================================

class TestOcistiIstoriju:
    """Testovi za ocisti_istoriju funkciju."""

    def test_clears_history(self):
        """Testira brisanje istorije."""
        HISTORY.append({"role": "user", "content": "Test"})
        assert len(HISTORY) == 1
        ocisti_istoriju()
        assert len(HISTORY) == 0

    def test_empty_history(self):
        """Testira brisanje prazne istorije."""
        ocisti_istoriju()
        assert len(HISTORY) == 0


# ============================================================
# TESTIRANJE sacuvaj_istoriju()
# ============================================================

class TestSacuvajIstoriju:
    """Testovi za sacuvaj_istoriju funkciju."""

    def test_saves_history(self):
        """Testira čuvanje istorije."""
        HISTORY.append({"role": "user", "content": "Test"})
        HISTORY.append({"role": "assistant", "content": "Odgovor"})
        f = sacuvaj_istoriju()
        assert f.exists()
        data = json.loads(f.read_text(encoding="utf-8"))
        assert len(data) == 2
        # Cleanup
        f.unlink()


# ============================================================
# TESTIRANJE KONSTANTI
# ============================================================

class TestConstants:
    """Testovi za konstante."""

    def test_ollama_url(self):
        """Testira OLLAMA_URL."""
        assert "11434" in OLLAMA_URL

    def test_model_not_empty(self):
        """Testira da model nije prazan."""
        assert MODEL != ""
