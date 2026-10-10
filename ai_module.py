"""
Ollama AI adapter za DRAŽEN AI.
Priča sa lokalnim Ollama serverom (127.0.0.1:11434).
"""
import json
import sys

import requests

from config import CFG, ROOT

OLLAMA_URL = CFG["ollama"]["url"].rstrip("/")
MODEL = CFG["ollama"]["model"]
TIMEOUT = CFG["ollama"]["timeout"]
SYSTEM_PROMPT = CFG["ollama"]["system_prompt"]

HISTORY: list[dict] = []


def proveri_vezu() -> tuple[bool, str]:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        modeli = [m["name"] for m in r.json().get("models", [])]
        if not modeli:
            return False, "Nema instaliranih modela."
        if not any(MODEL.split(":")[0] in m for m in modeli):
            return False, f"Model '{MODEL}' nije nađen."
        return True, f"OK — model: {MODEL}"
    except requests.exceptions.ConnectionError:
        return False, f"Ne mogu da se povežem na {OLLAMA_URL}."
    except Exception as e:
        return False, f"Greška: {e}"


def lista_modela() -> list[str]:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def pitaj(prompt: str, stream: bool = True) -> str:
    HISTORY.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + HISTORY,
        "stream": stream,
    }

    try:
        if stream:
            return _pitaj_stream(payload)
        return _pitaj_ceo(payload)
    except requests.exceptions.Timeout:
        return "⚠️ Ollama ne odgovara (timeout)."
    except requests.exceptions.ConnectionError:
        return f"⚠️ Ne mogu da se povežem na {OLLAMA_URL}."
    except Exception as e:
        return f"⚠️ Greška: {e}"


def _pitaj_stream(payload: dict) -> str:
    full = []
    with requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        stream=True,
        timeout=TIMEOUT,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            deo = chunk.get("message", {}).get("content", "")
            if deo:
                print(deo, end="", flush=True)
                full.append(deo)
            if chunk.get("done"):
                break
    print()
    odgovor = "".join(full)
    HISTORY.append({"role": "assistant", "content": odgovor})
    return odgovor


def _pitaj_ceo(payload: dict) -> str:
    payload["stream"] = False
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    odgovor = r.json().get("message", {}).get("content", "")
    print(odgovor)
    HISTORY.append({"role": "assistant", "content": odgovor})
    return odgovor


def ocisti_istoriju() -> None:
    HISTORY.clear()


def sacuvaj_istoriju():
    f = ROOT / "ai_history.json"
    f.write_text(json.dumps(HISTORY, indent=2, ensure_ascii=False), encoding="utf-8")
    return f


def chat_loop() -> None:
    print("\n" + "=" * 56)
    print("  🤖 AI CHAT — 'exit' izlaz, 'clear' briše, 'save' čuva")
    print("  'model' menja model, 'models' lista modele")
    print("=" * 56)

    ok, msg = proveri_vezu()
    print(f"Status: {msg}")
    if not ok:
        return

    while True:
        try:
            q = input("\nTi: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nIzlaz iz AI chata.")
            return

        if not q:
            continue
        if q.lower() in ("exit", "quit", "izlaz"):
            return
        if q.lower() in ("clear", "ocisti"):
            ocisti_istoriju()
            print("Istorija obrisana.")
            continue
        if q.lower() == "save":
            f = sacuvaj_istoriju()
            print(f"Sačuvano: {f}")
            continue
        if q.lower() == "models":
            print("Dostupni modeli:")
            for m in lista_modela():
                print(f"  - {m}")
            continue

        print("\nAI: ", end="", flush=True)
        pitaj(q)
