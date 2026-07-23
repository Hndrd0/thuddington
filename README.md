# Thuddington (Thump-Shortcut)

A hands-free Windows application that maps desktop thumps/knocks detected via your microphone to custom keyboard shortcuts and executable commands. 

Built with **PySide6 (Qt)**, **sounddevice**, and **numpy** for clean real-time onset energy detection.

## Features

- **Microphone-Triggered Actions**: Tap your desk to trigger shortcuts (e.g. 1 thump -> notepad, 2 thumps -> calculator).
- **Tray-Based UI**: Runs silently in the Windows system tray with status-reactive icons.
- **Dynamic Configuration**: Adjustable sensitivity sliders and customizable thump count mappings in a Qt-styled Settings panel.
- **Global Hotkey Activation**: Uses a system-wide hotkey (`Ctrl+Shift+Space` by default) to start the listening window.

## Requirements

- Windows 10/11
- Python 3.12+ (if running from source)
- Core dependencies: `PySide6`, `sounddevice`, `numpy`, `keyboard`

## Development & Usage

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Locally**:
   ```bash
   python main.py
   ```

3. **Global Hotkey Workflow**:
   - Press `Ctrl+Shift+Space` to put the app in listening mode.
   - Tap/thump your desk within 2 seconds.
   - The mapped command will execute based on the thump count.

## Building standalone .exe

An automated Python build script `build.py` compiles the application into a single executable file:
```bash
python build.py
```
This packages the app into `dist/ThumpShortcut.exe` using PyInstaller.
