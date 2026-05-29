# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['/Users/gesche/jarvis'],
    binaries=[],
    datas=[
        ('.env.example', '.'),
        ('web', 'web'),          # Chat-UI mit einbinden
    ],
    hiddenimports=[
        'faster_whisper',
        'sounddevice',
        'numpy',
        'openai',
        'httpx',
        'chromadb',
        'sentence_transformers',
        'fastapi',
        'fastapi.staticfiles',
        'fastapi.responses',
        'aiofiles',
        'uvicorn',
        'uvicorn.lifespan.on',
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'webview',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JARVIS',
    debug=False,
    strip=False,
    upx=False,
    console=False,       # Kein Terminal-Fenster
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='JARVIS',
)

app = BUNDLE(
    coll,
    name='JARVIS.app',
    icon=None,
    bundle_identifier='de.notenstudio.jarvis',
    info_plist={
        'NSMicrophoneUsageDescription': 'JARVIS braucht das Mikrofon für Sprachsteuerung.',
        'CFBundleShortVersionString': '3.1.0',
        'CFBundleVersion': '3.1.0',
        'LSMinimumSystemVersion': '12.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
    },
)
