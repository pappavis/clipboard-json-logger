from setuptools import setup

APP = ["src/clipboard_json_logger.py"]
OPTIONS = {
    "argv_emulation": True,
    "packages": [],
    "plist": {
        "CFBundleName": "ClipboardJsonLogger",
        "CFBundleDisplayName": "Clipboard JSON Logger",
        "CFBundleIdentifier": "com.michiel.clipboardjsonlogger",
        "CFBundleShortVersionString": "0.4.0",
        "CFBundleVersion": "0.4.0",
        "LSUIElement": True,  # menu bar app (no dock icon)
    },
}

setup(
    name="clipboard-json-logger",
    version="0.4.0",
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)