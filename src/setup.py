## `setup.py`

from setuptools import setup

APP = ["src/clipboard_json_logger.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "Clipboard JSON Logger",
        "CFBundleDisplayName": "Clipboard JSON Logger",
        "CFBundleIdentifier": "com.example.clipboard-json-logger",
        "CFBundleShortVersionString": "0.5.0",
        "CFBundleVersion": "0.5.0",
        # Menu bar app (no Dock icon)
        "LSUIElement": True,
    },
    # If you end up needing explicit packages/includes, add here.
}

setup(
    name="clipboard-json-logger",
    version="0.5.0",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)