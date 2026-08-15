import argparse
from collections.abc import Callable
import os
from pathlib import Path
import socket
import sys
import threading
import time
import webbrowser

import uvicorn


FROZEN = bool(getattr(sys, "frozen", False))
APP_ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent.parent
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", APP_ROOT))


def find_available_port(host: str, preferred_port: int, attempts: int = 20) -> int:
    if not 1 <= preferred_port <= 65535 or attempts < 1:
        raise ValueError("連接埠必須介於 1-65535，且嘗試次數至少為 1。")
    last_port = min(65535, preferred_port + attempts - 1)
    for port in range(preferred_port, last_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            try:
                candidate.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(
        f"找不到可用連接埠（已檢查 {preferred_port}-{last_port}）。"
    )


def open_browser_when_ready(
    server: uvicorn.Server,
    url: str,
    opener: Callable[[str], object] = webbrowser.open,
    timeout: float = 30.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if server.started:
            opener(url)
            return
        if server.should_exit:
            return
        time.sleep(0.1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="啟動 MaterialRAG")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MATERIALRAG_PORT", "8000")),
        help="優先使用的連接埠（預設：8000）",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="啟動後不要自動開啟瀏覽器",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frontend = BUNDLE_ROOT / "dist" / "index.html"
    if not frontend.is_file():
        raise SystemExit("找不到正式前端，請先執行 npm run build。")

    if FROZEN:
        os.environ.setdefault("MATERIALRAG_FRONTEND_PATH", str(frontend.parent))
        os.environ.setdefault("MATERIALRAG_INDEX_PATH", str(APP_ROOT / "data" / "chroma"))

    host = "127.0.0.1"
    port = find_available_port(host, args.port)
    url = f"http://{host}:{port}"
    env_file = APP_ROOT / ".env.local"
    config = uvicorn.Config(
        "backend.main:app",
        host=host,
        port=port,
        env_file=str(env_file) if env_file.is_file() else None,
    )
    server = uvicorn.Server(config)

    if not args.no_browser:
        threading.Thread(
            target=open_browser_when_ready,
            args=(server, url),
            daemon=True,
        ).start()

    print(f"MaterialRAG：{url}")
    server.run()


if __name__ == "__main__":
    main()
