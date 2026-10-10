"""
DRAŽEN AI — TERMUX V3
Kategorija 8 (mrežni napadi) DOZVOLJENA
Sve ostalo blokirano
"""

from pathlib import Path
import os
import shutil
import datetime
import subprocess
import re
import sys

# ============================================================
# KONFIGURACIJA
# ============================================================
ROOT = Path(__file__).resolve().parent
LOG = ROOT / "activity.log"
MAX_TIMEOUT = 60

# ============================================================
# OPASNE KOMANDE — BLOKIRAJ
# ============================================================
OPASNE_KOMANDE = [
    # 1. BRISANJE
    r"rm\s+-rf\s+/", r"rm\s+-rf\s+/\*", r"rm\s+-rf\s+~",
    r"rm\s+-rf\s+/sdcard", r"rm\s+-rf\s+/data",
    r"find\s+/\s+-delete", r"shred\s+-uz\s+/",

    # 2. FORMATIRANJE
    r"mkfs", r"dd\s+if=", r"fdisk", r"parted",

    # 3. FORK BOMBE
    r":\(\)\{", r"^\s*yes\s*$", r"cat\s+/dev/zero",
    r"while\s+true", r"perl\s+-e\s+['\"]fork",

    # 4. PREUSMERAVANJE
    r">\s*/dev/sda", r">\s*/etc/passwd", r">\s*/etc/shadow",
    r"chmod\s+-R\s+000\s+/",

    # 5. SISTEMSKI FOLDERI
    r"rm\s+-rf\s+/system", r"rm\s+-rf\s+/boot",
    r"rm\s+-rf\s+/etc", r"rm\s+-rf\s+/usr",
    r"rm\s+-rf\s+/var", r"rm\s+-rf\s+/root",

    # 6. GAŠENJE
    r"^\s*reboot\s*$", r"^\s*poweroff\s*$",
    r"^\s*shutdown", r"^\s*halt\s*$", r"^\s*init\s+0",

    # 7. KORISNICI
    r"userdel", r"passwd\s+-d", r"usermod\s+-L", r"chpasswd",

    # 9. KRADA PODATAKA
    r"cat\s+/etc/shadow", r"grep\s+-r\s+password",
    r"find\s+/\s+-name\s+['\"]?\*\.key",
    r"curl\s+-X\s+POST.*@/etc",

    # 10. SKRIVENO IZVRŠAVANJE
    r"eval\s+\$\(", r"base64\s+-d.*\|\s*sh",
    r"curl.*\|\s*sh", r"wget.*\|\s*sh",
    r"curl.*\|\s*bash", r"wget.*\|\s*bash",
    r"bash\s+-i\s+>&", r"nc\s+-e", r"ncat\s+-e",
    r"socat.*exec", r"/dev/tcp/",
]


def log(msg: str) -> None:
    try:
        line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def pause() -> None:
    try:
        input("\nPritisni Enter za nastavak...")
    except (KeyboardInterrupt, EOFError):
        print("\nIzlaz...")
        sys.exit(0)


def banner() -> None:
    print("\n" + "=" * 56)
    print("             DRAŽEN AI — TERMUX V3")
    print("=" * 56)


def is_opasna(cmd: str) -> str | None:
    for pattern in OPASNE_KOMANDE:
        if re.search(pattern, cmd, re.IGNORECASE):
            return pattern
    return None


def safe_path(user_input: str):
    try:
        p = Path(user_input).expanduser().resolve()
        return p
    except Exception as e:
        print(f"Greška u putanji: {e}")
        return None


def system_info() -> None:
    print("\n--- Sistem ---")
    print("Home:", Path.home())
    print("Radni folder:", ROOT)
    print("Python:", sys.version.split()[0])
    try:
        u = shutil.disk_usage(Path.home())
        print(f"Slobodan prostor: {u.free / 1024**3:.2f} GB")
    except Exception as e:
        print("Disk info:", e)
    log("Pregled sistema")


def organize() -> None:
    src = input("Putanja foldera za organizovanje: ").strip()
    p = safe_path(src)
    if not p or not p.is_dir():
        print("Folder ne postoji.")
        return

    out = p / "Organizovano"
    out.mkdir(exist_ok=True)

    cats = {
        "Dokumenti": {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf"},
        "Slike": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"},
        "Video": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
        "Audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a"},
        "Arhive": {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z"},
    }

    n = 0
    try:
        for x in p.iterdir():
            if not x.is_file():
                continue
            cat = next((k for k, v in cats.items() if x.suffix.lower() in v), "Ostalo")
            d = out / cat
            d.mkdir(exist_ok=True)
            target = d / x.name
            i = 1
            while target.exists():
                target = d / f"{x.stem}_{i}{x.suffix}"
                i += 1
            shutil.copy2(x, target)
            n += 1
    except Exception as e:
        print(f"Greška: {e}")

    print(f"Gotovo. Kopirano: {n}.")
    log(f"Organizovan folder: {p}, fajlova: {n}")


def find_large() -> None:
    src = input("Folder za pretragu: ").strip()
    p = safe_path(src)
    if not p or not p.is_dir():
        print("Folder ne postoji.")
        return

    found = []
    try:
        for x in p.rglob("*"):
            try:
                if x.is_file():
                    mb = x.stat().st_size / 1024**2
                    if mb >= 100:
                        found.append((mb, x))
            except OSError:
                pass
    except Exception as e:
        print(f"Greška: {e}")
        return

    found.sort(reverse=True)
    print("\nNajveći fajlovi (>=100 MB):")
    for mb, x in found[:50]:
        print(f"{mb:9.1f} MB  {x}")
    print(f"Ukupno pronađeno: {len(found)}")
    log(f"Pretraga velikih fajlova: {p}")


def search_files() -> None:
    base = input("Folder za pretragu: ").strip()
    term = input("Naziv/tekst koji tražiš: ").strip().lower()
    p = safe_path(base)
    if not p or not p.is_dir():
        print("Folder ne postoji.")
        return

    matches = []
    try:
        for x in p.rglob("*"):
            try:
                if x.is_file() and term in x.name.lower():
                    matches.append(x)
            except OSError:
                pass
    except Exception as e:
        print(f"Greška: {e}")
        return

    print(f"\nPronađeno: {len(matches)}")
    for x in matches[:100]:
        print(x)
    log(f"Pretraga: {term} u {p}")


def text_stats() -> None:
    p = safe_path(input("Putanja tekstualnog fajla: ").strip())
    if not p or not p.is_file():
        print("Fajl ne postoji.")
        return

    try:
        s = p.read_text(encoding="utf-8", errors="replace")
        words = s.split()
        print(f"\nKaraktera: {len(s)}")
        print(f"Reči: {len(words)}")
        print(f"Linija: {len(s.splitlines())}")
        print(f"Veličina: {p.stat().st_size / 1024:.1f} KB")
        log(f"Analiziran tekst: {p}")
    except Exception as e:
        print(f"Greška: {e}")


def shell_command() -> None:
    print("\nOvo izvršava komandu koju TI uneseš.")
    print("Mrežni napadi su DOZVOLJENI.")
    print("Ostale opasne komande su blokirane.")

    try:
        cmd = input("$ ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if not cmd:
        return

    razlog = is_opasna(cmd)
    if razlog:
        print(f"\n⚠️ OPASNA KOMANDA BLOKIRANA!")
        print(f"Razlog: {razlog}")
        log(f"BLOKIRANA komanda: {cmd}")
        return

    print(f"\nKomanda: {cmd}")
    try:
        if input("Izvrši? (da/ne): ").strip().lower() != "da":
            print("Otkazano.")
            return
    except (KeyboardInterrupt, EOFError):
        return

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            timeout=MAX_TIMEOUT,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        log(f"Izvršena komanda: {cmd}")
    except subprocess.TimeoutExpired:
        print(f"⚠️ Komanda je prekoračila {MAX_TIMEOUT} sekundi.")
        log(f"TIMEOUT: {cmd}")
    except Exception as e:
        print(f"Greška: {e}")
        log(f"GREŠKA: {cmd} — {e}")


def ai() -> None:
    """AI modul — poziva Ollama chat."""
    from ai_module import chat_loop
    chat_loop()


def show_log() -> None:
    """Prikazuje activity log."""
    if LOG.exists():
        print(LOG.read_text(encoding="utf-8"))
    else:
        print("Log je prazan.")


# ============================================================
# MENI
# ============================================================
def menu() -> None:
    """Glavni meni."""
    while True:
        banner()
        print("""
[1] 🤖 AI pomoćnik
[2] 📁 Organizuj fajlove
[3] 🔎 Pretraži fajlove
[4] 📄 Analiziraj tekst
[5] 📊 Sistem / prostor
[6] 🧹 Pronađi velike fajlove
[7] 🖥️ Ručna Termux komanda
[8] 📋 Activity log
[0] Izlaz
""")
        try:
            c = input("Izaberi: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nIzlaz...")
            break

        if c == "1":
            ai()
        elif c == "2":
            organize()
        elif c == "3":
            search_files()
        elif c == "4":
            text_stats()
        elif c == "5":
            system_info()
        elif c == "6":
            find_large()
        elif c == "7":
            shell_command()
        elif c == "8":
            show_log()
        elif c == "0":
            print("\nDoviđenja!")
            break
        else:
            print("Nepoznata opcija.")

        pause()


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nIzlaz...")
