# build.py
import subprocess
import os
import sys
from pathlib import Path

def build():
    project_dir = Path(__file__).parent.resolve()
    
    # We will build a single EXE, windowed (no console window)
    cmd = [
        "python", "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name=ThumpShortcut",
        # Include assets folder, config.json, and tokens.css
        f"--add-data=assets{os.pathsep}assets",
        f"--add-data=config.json{os.pathsep}.",
        f"--add-data=tokens.css{os.pathsep}.",
        f"--add-data=shortcuts.py{os.pathsep}.",
        f"--add-data=thud_detector.py{os.pathsep}.",
        # keyboard library needs admin privileges on Windows to hook keypresses
        # sometimes packaging needs hidden imports for PySide6 elements
        "--collect-data", "PySide6",
        "--collect-submodules", "PySide6.QtCore",
        "--collect-submodules", "PySide6.QtGui",
        "--collect-submodules", "PySide6.QtWidgets",
        "main.py"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_dir)
    
    if result.returncode == 0:
        print("\n✓ Standalone build completed successfully.")
        print(f"Exe created at: {project_dir / 'dist' / 'ThumpShortcut.exe'}")
    else:
        print("\n✗ Build failed")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build()
