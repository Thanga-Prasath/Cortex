#!/usr/bin/env python3
"""
Cortex Launcher — Gacha-style model downloader + auto-updater
Like a game launcher: small installer, large assets downloaded on first run.
"""

import sys
import os
import json
import platform
import subprocess
import threading
import requests
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette

# ─── Constants ────────────────────────────────────────────────────────────────

GITHUB_REPO    = "Thanga-Prasath/Cortex"
GITHUB_API     = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
VERSION_FILE   = Path(__file__).parent / "version.txt"
APP_DIR        = Path(__file__).parent

# Model download destinations (user home, not app dir)
MODELS_DIR     = Path.home() / ".cortex" / "models"
PIPER_DIR      = Path.home() / ".cortex" / "piper_engine"

# Model download URLs (update these when you host model packs on GitHub Releases)
MODEL_URLS = {
    "whisper": {
        "url": f"https://github.com/{GITHUB_REPO}/releases/download/models/whisper-base-en.tar.gz",
        "dest": MODELS_DIR / "whisper",
        "label": "Whisper Speech Model",
        "size_mb": 150,
    },
    "piper": {
        "url": f"https://github.com/{GITHUB_REPO}/releases/download/models/piper_engine_linux.tar.gz",
        "dest": PIPER_DIR,
        "label": "Piper TTS Engine",
        "size_mb": 210,
    },
}

def read_local_version() -> str:
    try:
        return VERSION_FILE.read_text().strip()
    except Exception:
        return "v0.0.0"

def get_os_asset_suffix() -> str:
    system = platform.system()
    if system == "Windows":
        return "-Windows.exe"
    elif system == "Linux":
        return "_amd64.deb"
    return ""


# ─── Background Workers ────────────────────────────────────────────────────────

class UpdateChecker(QThread):
    """Checks GitHub API for a newer version."""
    result = pyqtSignal(str, str)   # (tag_name, download_url) — empty strings if up-to-date
    error  = pyqtSignal(str)

    def run(self):
        try:
            r = requests.get(GITHUB_API, timeout=10)
            r.raise_for_status()
            data = r.json()
            latest_tag = data["tag_name"]
            local_tag  = read_local_version()

            if latest_tag != local_tag:
                suffix = get_os_asset_suffix()
                url = ""
                for asset in data.get("assets", []):
                    if asset["name"].endswith(suffix):
                        url = asset["browser_download_url"]
                        break
                self.result.emit(latest_tag, url)
            else:
                self.result.emit("", "")
        except Exception as e:
            self.error.emit(str(e))


class DownloadWorker(QThread):
    """Downloads a file streaming with progress updates."""
    progress = pyqtSignal(int, float)  # (percent, MB/s)
    done     = pyqtSignal(Path)
    error    = pyqtSignal(str)

    def __init__(self, url: str, dest_path: Path):
        super().__init__()
        self.url       = url
        self.dest_path = dest_path

    def run(self):
        import time
        try:
            self.dest_path.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(self.url, stream=True, timeout=30)
            r.raise_for_status()

            total    = int(r.headers.get("content-length", 0))
            received = 0
            start    = time.time()

            with open(self.dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        received += len(chunk)
                        elapsed  = max(time.time() - start, 0.001)
                        speed    = (received / elapsed) / 1_048_576  # MB/s
                        pct      = int(received * 100 / total) if total else 0
                        self.progress.emit(pct, speed)

            self.done.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))


# ─── Main Launcher Window ──────────────────────────────────────────────────────

class CortexLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._start_check()

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setWindowTitle("Cortex Launcher")
        self.setFixedSize(560, 340)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Outer container
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Main card frame
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("""
            QFrame#card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0f1a, stop:1 #1a1a2e);
                border-radius: 18px;
                border: 1px solid rgba(100, 80, 255, 0.35);
            }
        """)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 30, 36, 28)
        layout.setSpacing(0)

        # ── Header row ────────────────────────────────────────────────────────
        header = QHBoxLayout()

        # Logo
        icon_label = QLabel()
        icon_path  = APP_DIR / "icon.png"
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pix)
        header.addWidget(icon_label)
        header.addSpacing(14)

        # Name + version
        name_col = QVBoxLayout()
        name_col.setSpacing(2)

        title = QLabel("CORTEX")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        title.setStyleSheet("color: #c9b3ff; letter-spacing: 5px;")
        name_col.addWidget(title)

        self.ver_label = QLabel(f"Version {read_local_version()}")
        self.ver_label.setStyleSheet("color: #7a6faa; font-size: 12px;")
        name_col.addWidget(self.ver_label)

        header.addLayout(name_col)
        header.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.06); border-radius:14px;
                          color:#aaa; border:none; font-size:14px; }
            QPushButton:hover { background: rgba(255,80,80,0.25); color:white; }
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        layout.addLayout(header)
        layout.addSpacing(24)

        # ── Status label ──────────────────────────────────────────────────────
        self.status_label = QLabel("Connecting to update server…")
        self.status_label.setStyleSheet("color: #8888bb; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.status_label)
        layout.addSpacing(10)

        # ── Progress bar ──────────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar { background: rgba(255,255,255,0.06);
                           border-radius: 5px; border: none; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #6c4bff, stop:1 #c47fff);
                border-radius: 5px; }
        """)
        layout.addWidget(self.progress)
        layout.addSpacing(6)

        # Speed + ETA row
        info_row = QHBoxLayout()
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("color: #6a6a99; font-size: 11px;")
        self.eta_label = QLabel("")
        self.eta_label.setStyleSheet("color: #6a6a99; font-size: 11px;")
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        info_row.addWidget(self.speed_label)
        info_row.addWidget(self.eta_label)
        layout.addLayout(info_row)

        layout.addStretch()

        # ── Launch button ─────────────────────────────────────────────────────
        self.launch_btn = QPushButton("LAUNCH")
        self.launch_btn.setFixedHeight(46)
        self.launch_btn.setEnabled(False)
        self.launch_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #6c4bff, stop:1 #a855f7);
                color: white; border: none; border-radius: 12px;
                font-size: 15px; font-weight: bold; letter-spacing: 3px;
            }
            QPushButton:hover  { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #7c5dff, stop:1 #ba68fc); }
            QPushButton:disabled { background: rgba(100,80,200,0.25); color: #555577; }
        """)
        self.launch_btn.clicked.connect(self._launch_app)
        layout.addWidget(self.launch_btn)

        # Allow dragging the borderless window
        self._drag_pos = None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    # ── Update check ──────────────────────────────────────────────────────────

    def _start_check(self):
        self.checker = UpdateChecker()
        self.checker.result.connect(self._on_update_checked)
        self.checker.error.connect(self._on_update_error)
        self.checker.start()

    def _on_update_checked(self, tag: str, url: str):
        if tag:
            self.status_label.setText(f"🔄  Update available: {tag}  —  downloading…")
            self._download_file(url, APP_DIR / Path(url).name, on_done=self._on_update_done)
        else:
            self.status_label.setText("✅  Cortex is up to date.")
            self._check_models()

    def _on_update_error(self, msg: str):
        self.status_label.setText("⚠️  Offline — skipping update check.")
        self._check_models()

    def _on_update_done(self, path: Path):
        """Apply installer update — re-launch installer then quit."""
        self.status_label.setText("✅  Update downloaded. Applying…")
        system = platform.system()
        if system == "Linux":
            subprocess.Popen(["pkexec", "dpkg", "-i", str(path)])
        elif system == "Windows":
            subprocess.Popen([str(path), "/silent"])
        QApplication.quit()

    # ── Model check & download ─────────────────────────────────────────────────

    def _check_models(self):
        missing = [k for k, v in MODEL_URLS.items() if not v["dest"].exists()]
        if missing:
            self._download_models(missing)
        else:
            self.status_label.setText("✅  All systems ready.")
            self.progress.setValue(100)
            self.launch_btn.setEnabled(True)

    def _download_models(self, keys: list):
        self._model_queue = list(keys)
        self._download_next_model()

    def _download_next_model(self):
        if not self._model_queue:
            self.status_label.setText("✅  All assets ready.")
            self.progress.setValue(100)
            self.launch_btn.setEnabled(True)
            return

        key  = self._model_queue.pop(0)
        info = MODEL_URLS[key]
        self.status_label.setText(f"⬇️  Downloading {info['label']}  (~{info['size_mb']} MB)…")
        dest = info["dest"] / Path(info["url"]).name
        self._download_file(info["url"], dest, on_done=lambda p: self._on_model_done(p, key))

    def _on_model_done(self, path: Path, key: str):
        # Extract tar.gz
        import tarfile
        dest_dir = MODEL_URLS[key]["dest"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            with tarfile.open(path) as tar:
                tar.extractall(dest_dir)
            path.unlink(missing_ok=True)
        except Exception:
            pass
        self._download_next_model()

    # ── Generic download with progress ────────────────────────────────────────

    def _download_file(self, url: str, dest: Path, on_done):
        self.progress.setValue(0)
        self._dl = DownloadWorker(url, dest)
        self._dl.progress.connect(self._on_dl_progress)
        self._dl.done.connect(on_done)
        self._dl.error.connect(self._on_dl_error)
        self._dl.start()

    def _on_dl_progress(self, pct: int, speed: float):
        self.progress.setValue(pct)
        self.speed_label.setText(f"{speed:.1f} MB/s")
        remaining = 0
        total_mb  = 0
        # Try to show remaining
        for v in MODEL_URLS.values():
            if not v["dest"].exists():
                total_mb += v["size_mb"]
        done_mb = total_mb * pct / 100
        if speed > 0:
            remaining = int((total_mb - done_mb) / speed)
        self.eta_label.setText(f"ETA {remaining}s" if remaining > 0 else "")

    def _on_dl_error(self, msg: str):
        self.status_label.setText(f"⚠️  Download failed: {msg}")
        # Still allow launch with missing models (app handles gracefully)
        self.launch_btn.setEnabled(True)

    # ── Launch ────────────────────────────────────────────────────────────────

    def _launch_app(self):
        self.launch_btn.setEnabled(False)
        self.status_label.setText("🚀  Launching Cortex…")

        # Point app to user model dirs via environment
        env = os.environ.copy()
        env["CORTEX_MODELS_DIR"] = str(MODELS_DIR)
        env["CORTEX_PIPER_DIR"]  = str(PIPER_DIR)

        main_py = APP_DIR / "main.py"
        python  = sys.executable
        subprocess.Popen([python, str(main_py)], env=env)

        QTimer.singleShot(800, QApplication.quit)


# ─── Entry Point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = CortexLauncher()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
