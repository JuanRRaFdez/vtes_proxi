# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


def _collect_tree(src_dir: str, prefix: str):
    """Devuelve una lista de tuplas (src, dest) para Analysis.datas."""
    src_path = Path(src_dir)
    if not src_path.exists():
        return []
    collected = []
    for file_path in src_path.rglob('*'):
        if not file_path.is_file():
            continue
        rel_parent = file_path.relative_to(src_path).parent
        dest_dir = str(Path(prefix) / rel_parent)
        collected.append((str(file_path), dest_dir))
    return collected


datas = (
    _collect_tree('config', 'config')
    + _collect_tree('resources', 'resources')
    + _collect_tree('fonts', 'fonts')
)


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
