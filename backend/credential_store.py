import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _settings_path() -> Path:
    root = os.getenv("LOCALAPPDATA")
    if not root:
        raise RuntimeError("Windows LOCALAPPDATA is unavailable")
    return Path(root) / "MaterialRAG" / "gemini.json"


def _blob(data: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data)
    return (
        _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))),
        buffer,
    )


def _protect(data: bytes) -> bytes:
    source, source_buffer = _blob(data)
    destination = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptProtectData(
        ctypes.byref(source),
        "MaterialRAG Gemini API Key",
        None,
        None,
        None,
        0,
        ctypes.byref(destination),
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(destination.pbData)
        del source_buffer


def _unprotect(data: bytes) -> bytes:
    source, source_buffer = _blob(data)
    destination = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(destination)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(destination.pbData)
        del source_buffer


def save_gemini_configuration(api_key: str, model: str) -> None:
    payload = json.dumps({"api_key": api_key, "model": model}).encode("utf-8")
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(base64.b64encode(_protect(payload)).decode("ascii"), encoding="ascii")
    os.replace(temporary, path)


def load_gemini_configuration() -> tuple[str, str] | None:
    path = _settings_path()
    if not path.exists():
        return None
    encrypted = base64.b64decode(path.read_text(encoding="ascii"), validate=True)
    payload = json.loads(_unprotect(encrypted).decode("utf-8"))
    api_key = str(payload.get("api_key", "")).strip()
    model = str(payload.get("model", "gemini-3.5-flash")).strip()
    return (api_key, model) if api_key and model else None
