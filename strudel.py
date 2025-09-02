import os
import re
import json
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/nucklearproject/samples/master/"
ROOT = Path(".").resolve()

# Directorios a ignorar
IGNORE_DIRS = {".git", "node_modules", "examples", "__pycache__", ".venv"}
# Extensiones permitidas para renombrar y para el JSON
ALLOW_EXTS = {".wav", ".flac", ".ogg"}

def safe_audio_name(filename: str) -> str:
    """
    Devuelve un nombre 'seguro' para audio:
    - Reemplaza espacios por '-'
    - Colapsa múltiples '-' consecutivos
    - Mantiene extensión original
    """
    p = Path(filename)
    stem = re.sub(r"\s+", "-", p.stem.strip())
    stem = re.sub(r"-{2,}", "-", stem)
    return f"{stem}{p.suffix}"

def rename_files():
    """
    Renombra todos los archivos de audio dentro del árbol, reemplazando espacios por '-'.
    Maneja colisiones añadiendo sufijos incrementales.
    """
    for dirpath, dirs, files in os.walk(ROOT, topdown=True):
        # Podar dirs ignorados/ocultos
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS]

        for fname in files:
            src = Path(dirpath) / fname
            if src.suffix.lower() not in ALLOW_EXTS:
                continue

            target_name = safe_audio_name(src.name)
            if target_name == src.name:
                continue  # ya está bien

            dst = src.with_name(target_name)

            # Si existe, buscar un nombre disponible: nombre-1.ext, -2.ext, ...
            if dst.exists():
                base = Path(target_name).stem
                ext = Path(target_name).suffix
                i = 1
                while True:
                    cand = src.with_name(f"{base}-{i}{ext}")
                    if not cand.exists():
                        dst = cand
                        break
                    i += 1

            # Renombrar
            print(f"[rename] '{src.name}' -> '{dst.name}'  en {src.parent}")
            src.rename(dst)

def generate_json():
    """
    Genera strudel.json después de renombrar, incluyendo wav, flac y ogg,
    agrupados por la carpeta inmediata que los contiene.
    Rutas con prefijo '/' y separadores POSIX.
    """
    data = {"_base": BASE_URL}

    for dirpath, dirs, files in os.walk(ROOT, topdown=True):
        # Podar dirs ignorados/ocultos
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS]

        rel_dir = Path(dirpath).relative_to(ROOT)
        if rel_dir == Path("."):
            continue

        name = rel_dir.name
        if name.startswith(".") or name in IGNORE_DIRS:
            continue

        items = []
        for f in files:
            p = Path(dirpath) / f
            if p.suffix.lower() in ALLOW_EXTS:
                rel = p.relative_to(ROOT).as_posix()
                items.append("/" + rel)

        if items:
            items.sort()
            data.setdefault(name, []).extend(items)

    with open(ROOT / "strudel.json", "w", encoding="utf-8", newline="\n") as fp:
        json.dump(data, fp, ensure_ascii=False, separators=(",", ":"))

if __name__ == "__main__":
    rename_files()
    generate_json()
    print("✅ Listongo: renombrados los archivos de audio y generado strudel.json")
