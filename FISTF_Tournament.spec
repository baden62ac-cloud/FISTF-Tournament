# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('logo.png', '.'), ('fistf_ko_engine.py', '.'), ('fistf_formulas_2_16.json', '.'), ('Categorie_ESEMPIO.xlsx', '.'), ('icon.ico', '.')]
binaries = []
hiddenimports = ['pandas', 'openpyxl', 'numpy', 'PIL', 'PIL._tkinter_finder', 'PIL.Image', 'PIL.ImageTk', 'tkinter', 'threading', 'subprocess', 'datetime', 'psutil']
tmp_ret = collect_all('PIL')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['gui_fistf_tk.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='FISTF_Tournament',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=['icon.ico'],
    manifest='uac.manifest',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FISTF_Tournament',
)
