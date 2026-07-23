# main.py
import json
import os
import sys
import threading
import argparse
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Slot, QObject, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QWidget,
    QVBoxLayout,
    QLabel,
    QSlider,
    QPlainTextEdit,
    QPushButton,
    QMessageBox,
)

import keyboard   # global hotkey listener
from thud_detector import ThudDetector
from shortcuts import run_command

APP_ROOT = Path(__file__).parent.resolve()
CONFIG_PATH = APP_ROOT / "config.json"
TOKEN_PATH = APP_ROOT / "tokens.css"

# ------------------------------------------------------------
# Helper: load / save config
# ------------------------------------------------------------
def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "sensitivity": 0.4,
            "thunk_mappings": {"1": "notepad.exe", "2": "calc.exe", "3": "explorer.exe"},
            "hotkey": "ctrl+shift+space",
        }

def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

# ------------------------------------------------------------
# Settings UI
# ------------------------------------------------------------
class SettingsWindow(QWidget):
    def __init__(self, cfg: dict, on_save):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Thump-Shortcut Settings")
        self.setFixedSize(340, 260)
        self.cfg = cfg
        self.on_save = on_save
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Thump-Shortcut Settings")
        header.setObjectName("header")
        layout.addWidget(header)

        # Sensitivity slider
        s_lab = QLabel("Detection sensitivity (low -> high)")
        s_lab.setObjectName("sliderLabel")
        layout.addWidget(s_lab)
        self.sens_slider = QSlider(Qt.Horizontal)
        self.sens_slider.setRange(0, 100)
        self.sens_slider.setValue(int(self.cfg["sensitivity"] * 100))
        layout.addWidget(self.sens_slider)

        # Mapping editor
        m_lab = QLabel("Thump count -> command (one per line)")
        m_lab.setObjectName("mappingLabel")
        layout.addWidget(m_lab)
        self.mapping_edit = QPlainTextEdit()
        self.mapping_edit.setObjectName("mappingEdit")
        mapping_text = "\n".join(f"{k}:{v}" for k, v in self.cfg["thunk_mappings"].items())
        self.mapping_edit.setPlainText(mapping_text)
        layout.addWidget(self.mapping_edit)

        # Save button
        save_btn = QPushButton("Save & Apply")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    @Slot()
    def _save(self):
        self.cfg["sensitivity"] = self.sens_slider.value() / 100.0

        new_map = {}
        for line in self.mapping_edit.toPlainText().splitlines():
            if ":" in line:
                cnt, cmd = line.split(":", 1)
                cnt = cnt.strip()
                cmd = cmd.strip()
                if cnt.isdigit() and cmd:
                    new_map[cnt] = cmd
        if new_map:
            self.cfg["thunk_mappings"] = new_map

        save_config(self.cfg)
        self.on_save(self.cfg)
        QMessageBox.information(self, "Saved", "Settings saved successfully.")
        self.close()

# ------------------------------------------------------------
# Communication Bridge (Thread -> Qt Main Thread)
# ------------------------------------------------------------
class AppSignals(QObject):
    listening_started = Signal()
    thumps_detected = Signal(int)
    detection_error = Signal(str)

# ------------------------------------------------------------
# Tray app core
# ------------------------------------------------------------
class ThumpApp:
    def __init__(self, app):
        self.app = app
        self.signals = AppSignals()

        self.cfg = load_config()
        self.detector = ThudDetector(sensitivity=self.cfg["sensitivity"])
        
        self.icon_idle = QIcon(str(APP_ROOT / "assets" / "icon_idle.png"))
        self.icon_listen = QIcon(str(APP_ROOT / "assets" / "icon_listen.png"))
        self.icon_thump = QIcon(str(APP_ROOT / "assets" / "icon_thump.png"))

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon_idle)
        self.tray.setToolTip("Thump-Shortcut (idle)")

        # Build tray menu
        menu = QMenu()
        self.action_show = menu.addAction("Show Settings")
        self.action_quit = menu.addAction("Quit")
        self.tray.setContextMenu(menu)

        # Connections
        self.action_show.triggered.connect(self._open_settings)
        self.action_quit.triggered.connect(self._quit)
        self.tray.activated.connect(self._on_tray_activated)

        # Connect signals
        self.signals.listening_started.connect(self._on_listening_started)
        self.signals.thumps_detected.connect(self._on_thumps_detected)
        self.signals.detection_error.connect(self._on_detection_error)

        self.tray.show()

        # Register global hotkey
        keyboard.add_hotkey(self.cfg["hotkey"], self._trigger_hotkey)

        self.settings_win = None

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._open_settings()

    def _open_settings(self):
        if self.settings_win is None:
            self.settings_win = SettingsWindow(self.cfg, self._apply_new_config)
            self.settings_win.destroyed.connect(self._on_settings_destroyed)
        self.settings_win.show()

    def _on_settings_destroyed(self):
        self.settings_win = None

    def _apply_new_config(self, new_cfg):
        self.cfg = new_cfg
        self.detector.sensitivity = self.cfg["sensitivity"]
        keyboard.clear_all_hotkeys()
        keyboard.add_hotkey(self.cfg["hotkey"], self._trigger_hotkey)

    def _quit(self):
        keyboard.unhook_all()
        self.app.quit()

    def _trigger_hotkey(self):
        self.signals.listening_started.emit()
        threading.Thread(target=self._detect_thread, daemon=True).start()

    @Slot()
    def _on_listening_started(self):
        self.tray.setIcon(self.icon_listen)
        self.tray.setToolTip("Thump-Shortcut (listening)")

    def _detect_thread(self):
        try:
            thumps = self.detector.listen(duration=2.0)
            self.signals.thumps_detected.emit(thumps)
        except Exception as exc:
            print("[Thump] detection error:", exc)
            self.signals.detection_error.emit(str(exc))

    @Slot(str)
    def _on_detection_error(self, err_msg):
        self.tray.setIcon(self.icon_idle)
        self.tray.setToolTip("Thump-Shortcut (idle)")
        self.tray.showMessage(
            "Thump-Shortcut Error",
            f"Failed to record audio:\n{err_msg}",
            QSystemTrayIcon.Critical,
            5000,
        )

    @Slot(int)
    def _on_thumps_detected(self, thumps):
        self.tray.setIcon(self.icon_thump)
        self.tray.setToolTip(f"Detected {thumps} thump(s)")

        # Reset icon back to idle after 1s
        QTimer.singleShot(1000, lambda: self.tray.setIcon(self.icon_idle))
        QTimer.singleShot(1000, lambda: self.tray.setToolTip("Thump-Shortcut (idle)"))

        cmd = self.cfg["thunk_mappings"].get(str(thumps))
        if cmd:
            run_command(cmd)
        else:
            self.tray.showMessage(
                "Thump-Shortcut",
                f"{thumps} thump(s) – no command mapped",
                QSystemTrayIcon.Information,
                3000,
            )

# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thump-Shortcut tray app")
    parser.add_argument("--preview", action="store_true", help="Open settings window directly for UI preview")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)

    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    
    thump_app = ThumpApp(app)
    
    if args.preview:
        thump_app._open_settings()
        
    sys.exit(app.exec())
