# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


datas = [
    ("dist/index.html", "dist"),
    ("dist/assets", "dist/assets"),
]
for package in ("chromadb", "sentence_transformers", "transformers"):
    datas += collect_data_files(package)

a = Analysis(
    ["backend/launcher.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["backend.main", *collect_submodules("chromadb")],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MaterialRAG",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MaterialRAG",
)
