import os
import re
import json
import mimetypes
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# ---------- Config ----------
PORT = 5432
ROOT = Path(".").resolve()
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
ALLOW_EXTS = {".wav", ".flac", ".ogg"}  # renombrar y listar en JSON
JSON_NAME = "strudel.json"
# ----------------------------

def safe_audio_name(filename: str) -> str:
    """Reemplaza espacios por '-', colapsa '-' consecutivos, mantiene extensión."""
    p = Path(filename)
    stem = re.sub(r"\s+", "-", p.stem.strip())
    stem = re.sub(r"-{2,}", "-", stem)
    return f"{stem}{p.suffix}"

def rename_files():
    """Renombra wav/flac/ogg reemplazando espacios por '-' y resolviendo colisiones."""
    for dirpath, dirs, files in os.walk(ROOT, topdown=True):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS]
        for fname in files:
            src = Path(dirpath) / fname
            if src.suffix.lower() not in ALLOW_EXTS:
                continue
            target_name = safe_audio_name(src.name)
            if target_name == src.name:
                continue
            dst = src.with_name(target_name)
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
            print(f"[rename] {src.name} -> {dst.name}")
            src.rename(dst)

def generate_json(base_url: str = "http://localhost:5432/"):
    """
    Genera strudel.json (agrupado por carpeta inmediata). _base se escribirá con un valor
    placeholder local; igualmente el server lo reescribe dinámicamente al responder.
    """
    data = {"_base": base_url}
    for dirpath, dirs, files in os.walk(ROOT, topdown=True):
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
    with open(ROOT / JSON_NAME, "w", encoding="utf-8", newline="\n") as fp:
        json.dump(data, fp, ensure_ascii=False, separators=(",", ":"))
    print(f"[ok] {JSON_NAME} generado.")

class StrudelHandler(SimpleHTTPRequestHandler):
    # CORS
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _send_bytes(self, body: bytes, ctype="application/octet-stream"):
        try:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            if self.command != "HEAD":
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionAbortedError):
                    pass
        except Exception as e:
            self.send_error(500, f"Server error: {e}")

    def _send_file_streaming(self, path: Path, ctype="application/octet-stream"):
        try:
            size = path.stat().st_size
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(size))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            if self.command == "HEAD":
                return
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionAbortedError):
                        break
        except FileNotFoundError:
            self.send_error(404, "Not found")
        except Exception as e:
            self.send_error(500, f"Server error: {e}")

    def _serve_strudel_json(self):
        target = ROOT / JSON_NAME
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.send_error(404, f"No existe {JSON_NAME} en esta carpeta")
            return
        except Exception as e:
            self.send_error(500, f"No se pudo leer {JSON_NAME}: {e}")
            return

        # Reescribir _base dinámicamente con el Host real (localhost:5432, IP:puerto, etc.)
        host = self.headers.get("Host") or f"localhost:{PORT}"
        data["_base"] = f"http://{host}/"
        body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8")

    def do_GET(self):
        # Endpoint para reconstruir catálogo al vuelo: /rebuild
        if self.path.startswith("/rebuild"):
            # Opcional: volver a escanear y regenerar el JSON mientras el server corre
            try:
                rename_files()
                # base provisional: se reescribe al responder igualmente
                generate_json(base_url=f"http://localhost:{PORT}/")
                msg = b'{"ok":true,"message":"rebuild done"}'
                self._send_bytes(msg, "application/json; charset=utf-8")
            except Exception as e:
                self.send_error(500, f"rebuild error: {e}")
            return

        # / o /strudel.json -> devolver JSON con _base dinámico
        if self.path in ("/", f"/{JSON_NAME}"):
            self._serve_strudel_json()
            return

        # Archivos estáticos (audio, etc.)
        rel = self.path.lstrip("/").split("?", 1)[0].split("#", 1)[0]
        local = (ROOT / rel).resolve()

        # Evitar path traversal
        if not str(local).startswith(str(ROOT)):
            self.send_error(403, "Forbidden")
            return

        if local.is_file():
            ctype, _ = mimetypes.guess_type(str(local))
            if not ctype:
                ctype = "application/octet-stream"
            self._send_file_streaming(local, ctype)
            return

        # fallback del padre (404/listados si están habilitados)
        super().do_GET()

    def do_HEAD(self):
        if self.path in ("/", f"/{JSON_NAME}"):
            # calcular tamaño del JSON dinámico
            target = ROOT / JSON_NAME
            try:
                with open(target, "r", encoding="utf-8") as f:
                    data = json.load(f)
                host = self.headers.get("Host") or f"localhost:{PORT}"
                data["_base"] = f"http://{host}/"
                body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
            except Exception:
                return self.do_GET()
        else:
            return self.do_GET()

if __name__ == "__main__":
    # Paso 1: preparar catálogo en disco (misma lógica que tu primer script)
    rename_files()
    generate_json(base_url=f"http://localhost:{PORT}/")

    # Paso 2: server
    with ThreadingHTTPServer(("0.0.0.0", PORT), StrudelHandler) as server:
        print(f"Servidor corriendo en http://localhost:{PORT}/")
        print(f"- GET /           -> {JSON_NAME} (con _base dinámico)")
        print(f"- GET /{JSON_NAME} -> {JSON_NAME} (con _base dinámico)")
        print( "- GET /rebuild    -> renombra + regenera JSON al vuelo")
        server.serve_forever()
