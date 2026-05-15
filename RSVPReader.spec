# -*- mode: python ; coding: utf-8 -*-
import os
import site
from PyInstaller.utils.hooks import collect_all

# Locate llama_cpp native DLLs regardless of venv name.
_llama_lib = None
for _sp in site.getsitepackages():
    _candidate = os.path.join(_sp, 'llama_cpp', 'lib')
    if os.path.isdir(_candidate):
        _llama_lib = _candidate
        break

_llama_binaries = []
if _llama_lib:
    for _dll in os.listdir(_llama_lib):
        if _dll.endswith('.dll'):
            _llama_binaries.append((os.path.join(_llama_lib, _dll), 'llama_cpp/lib'))

_llama_datas, _llama_pkg_binaries, _llama_hiddenimports = collect_all('llama_cpp')
_llama_binaries.extend(_llama_pkg_binaries)

a = Analysis(
    ['backend\\desktop_main.py'],
    pathex=['backend'],
    binaries=_llama_binaries,
    datas=[('backend/static', 'static'), ('backend/build_version.txt', '.')] + _llama_datas,
    hiddenimports=[
        'llama_cpp',
        'llama_cpp.llama',
        'llama_cpp._internals',
    ] + _llama_hiddenimports + [
        'pystray._win32',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ImageColor',
    ],
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
    name='RSVPReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
