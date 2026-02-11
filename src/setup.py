from setuptools import setup

APP = ["clipboard_json_logger.py"]
OPTIONS = {
    "argv_emulation": True,
    "plist": {
        "CFBundleName": "ClipboardJsonLogger",
        "CFBundleDisplayName": "Clipboard JSON Logger",
        "CFBundleIdentifier": "com.yourname.clipboardjsonlogger",
        "CFBundleShortVersionString": "0.2.0",
    },
    "packages": [],
}

setup(
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
