# -*- mode: python ; coding: utf-8 -*-
# 4R022 Heart - PyInstaller spec  (Copyright (c) 2026 4R022 / Kaan Kross - 4R022 Heart License)
#
# Default output is a FOLDER build ("onedir"): the app starts instantly because nothing has to be
# unpacked at launch. Set HEART_ONEFILE=1 for a single-file exe (Windows/Linux) - slower to start,
# because it unpacks itself to a temp folder on every launch.
import os
import re
import sys
import tempfile

APP = "4R022-Heart"
ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))
ONEFILE = os.environ.get("HEART_ONEFILE") == "1"
IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

with open(os.path.join(ROOT, "Main", "Main.py"), encoding="utf-8") as fh:
    VERSION = re.search(r'__version__\s*=\s*"([^"]+)"', fh.read()).group(1)

icon = None
if IS_WIN:
    icon = os.path.join(ROOT, "Assets", "Icons", "icon.ico")
elif IS_MAC:
    icon = os.path.join(ROOT, "Assets", "Icons", "icon.icns")

# Only what the app needs at runtime (screenshots, logo sources, docs stay out -> smaller disk footprint)
datas = [
    (os.path.join(ROOT, "Assets", "Music"), "Assets/Music"),
    (os.path.join(ROOT, "Assets", "Icons", "icon.png"), "Assets/Icons"),
]

# Qt / Python parts the app never touches
EXCLUDES = [
    "tkinter", "unittest", "pydoc", "doctest", "test", "distutils", "setuptools", "pip",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets", "PySide6.QtQuickControls2",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtWebChannel", "PySide6.QtWebSockets", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtSvg", "PySide6.QtSvgWidgets", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtHelp",
    "PySide6.QtDesigner", "PySide6.QtUiTools", "PySide6.Qt3DCore", "PySide6.Qt3DRender",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DAnimation", "PySide6.Qt3DExtras",
    "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtBluetooth", "PySide6.QtNfc",
    "PySide6.QtSensors", "PySide6.QtSerialPort", "PySide6.QtPositioning", "PySide6.QtLocation",
    "PySide6.QtScxml", "PySide6.QtRemoteObjects", "PySide6.QtTextToSpeech", "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets", "PySide6.QtPrintSupport", "PySide6.QtXml", "PySide6.QtConcurrent",
]

a = Analysis(
    [os.path.join(ROOT, "Main", "Main.py")],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["PySide6.QtMultimedia"],
    hookspath=[],
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)

# Drop large Qt pieces a raster-only, offline app does not need.
DROP_LIBS = (
    "opengl32sw", "d3dcompiler", "qt6pdf", "qt6quick", "qt6qml", "qt6svg", "qt6virtualkeyboard",
    "qt6webengine", "qt63d", "qt6charts", "qt6datavisualization", "qt6sql", "qt6test", "qt6bluetooth",
    "qt6nfc", "qt6sensors", "qt6serialport", "qt6positioning", "qt6location", "qt6scxml",
    "qt6remoteobjects", "qt6texttospeech", "qt6designer", "qt6help",
)
DROP_DIRS = ("/imageformats/", "/iconengines/", "/generic/", "/tls/", "/networkinformation/",
             "/translations/", "/qml/")


def keep(item):
    name = item[0].replace("\\", "/").lower()
    base = os.path.basename(name)
    if not IS_MAC and any(base.startswith(d) or base.startswith("lib" + d) for d in DROP_LIBS):
        return False
    if any(d in "/" + name for d in DROP_DIRS):
        return False
    return True


a.binaries = [b for b in a.binaries if keep(b)]
a.datas = [d for d in a.datas if keep(d)]

pyz = PYZ(a.pure)

version_file = None
if IS_WIN:                                     # file properties shown by Windows Explorer
    nums = [int(x) for x in VERSION.split(".")][:4]
    nums += [0] * (4 - len(nums))
    vt = tuple(nums)
    version_file = os.path.join(tempfile.gettempdir(), "4r022_heart_version_info.txt")
    with open(version_file, "w", encoding="utf-8") as fh:
        fh.write(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={vt}, prodvers={vt}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', '4R022'),
      StringStruct('FileDescription', '4R022 Heart'),
      StringStruct('FileVersion', '{VERSION}'),
      StringStruct('InternalName', '4R022-Heart'),
      StringStruct('LegalCopyright', '(c) 2026 4R022 / Kaan Kross - 4R022 Heart License'),
      StringStruct('OriginalFilename', '4R022-Heart.exe'),
      StringStruct('ProductName', '4R022 Heart'),
      StringStruct('ProductVersion', '{VERSION}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ])
""")

if ONEFILE and not IS_MAC:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name=APP, debug=False, strip=False, upx=False,
              runtime_tmpdir=None, console=False, icon=icon, version=version_file)
else:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=APP, debug=False, strip=False, upx=False,
              console=False, icon=icon, version=version_file)
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name=APP)
    if IS_MAC:
        app = BUNDLE(coll, name=APP + ".app", icon=icon, bundle_identifier="com.4r022.heart",
                     version=VERSION,
                     info_plist={
                         "CFBundleName": "4R022 Heart",
                         "CFBundleDisplayName": "4R022 Heart",
                         "CFBundleShortVersionString": VERSION,
                         "CFBundleVersion": VERSION,
                         "NSHighResolutionCapable": True,
                         "LSMinimumSystemVersion": "11.0",
                         "NSHumanReadableCopyright": "(c) 2026 4R022 / Kaan Kross - 4R022 Heart License",
                     })
