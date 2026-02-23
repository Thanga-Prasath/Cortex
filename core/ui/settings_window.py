from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTabWidget, 
                             QMessageBox, QFrame, QFormLayout, QCheckBox,
                             QSlider, QColorDialog, QFileDialog, QComboBox)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
import json
import os
from .styles import get_stylesheet

class SettingsWindow(QMainWindow):
    def __init__(self, reset_event=None, status_window=None):
        super().__init__()
        self.reset_event = reset_event
        self.status_window = status_window
        self.setWindowTitle("Cortex Control - Settings")
        self.setGeometry(100, 100, 700, 500)
        
        # Data Setup
        self.config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
        self.widget_config_path = os.path.join(os.getcwd(), 'data', 'widget_config.json')
        self.config_data = self.load_config(self.config_path)
        self.widget_config = self.load_config(self.widget_config_path)
        
        # Apply Theme
        current_theme = self.config_data.get("theme", "Neon Green")
        from .styles import THEME_COLORS
        accent = THEME_COLORS.get(current_theme, "#39FF14")
        self.setStyleSheet(get_stylesheet(current_theme))
        
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        central.setLayout(main_layout)
        
        # Header
        header = QLabel("Cortex Control Center")
        header.setObjectName("Header")
        main_layout.addWidget(header)
        
        # Tabs - Dynamic Styling
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {accent}; background: #1e1e1e; }}
            QTabBar::tab {{ background: #2d2d30; color: #fff; padding: 10px; min-width: 100px; }}
            QTabBar::tab:selected {{ background: {accent}; color: #000; font-weight: bold; }}
        """)
        
        self.tab_general = QWidget()
        self.tab_voice = QWidget()
        # Removed redundant Theme tab
        
        self.tabs.addTab(self.tab_general, "General")
        self.tabs.addTab(self.tab_voice, "Voice")
        
        main_layout.addWidget(self.tabs)
        
        # --- Tab: General ---
        self.init_general_tab()
        
        # --- Tab: Voice ---
        self.init_voice_tab()

        # --- Footer Actions ---
        footer_layout = QHBoxLayout()
        
        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_reset.setStyleSheet("border: 1px solid #777; color: #aaa;")
        self.btn_reset.clicked.connect(self.reset_defaults)
        footer_layout.addWidget(self.btn_reset)
        
        footer_layout.addStretch()
        
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setMinimumWidth(150)
        self.btn_save.clicked.connect(self.save_settings)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("border: 1px solid #ff4444; color: #ff4444;")
        self.btn_cancel.clicked.connect(self.close)
        
        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_save)
        
        main_layout.addLayout(footer_layout)

    def load_config(self, path):
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def init_general_tab(self):
        layout = QFormLayout()
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)
        self.tab_general.setLayout(layout)
        
        # Name Field
        self.input_name = QLineEdit()
        self.input_name.setText(self.config_data.get("name", "Sir"))
        self.input_name.setPlaceholderText("What should I call you?")
        self.input_name.setStyleSheet("padding: 8px; background: #252526; border: 1px solid #555; color: #fff;")
        
        lbl_name = QLabel("Your Name:")
        self.input_name.textChanged.connect(self.on_name_changed)
        layout.addRow(lbl_name, self.input_name)
        
        # Theme Selector
        from PyQt6.QtWidgets import QComboBox
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Neon Green", "Cyber Blue", "Plasma Purple", "Fiery Red"])
        
        current_theme = self.config_data.get("theme", "Neon Green")
        index = self.combo_theme.findText(current_theme)
        if index >= 0:
            self.combo_theme.setCurrentIndex(index)
            
        self.combo_theme.setStyleSheet("padding: 8px; background: #252526; border: 1px solid #555; color: #fff;")
        
        lbl_theme = QLabel("Accent Theme:")
        self.combo_theme.currentTextChanged.connect(self.on_theme_changed)
        layout.addRow(lbl_theme, self.combo_theme)

        # Status GUI Enable
        self.chk_gui_enable = QCheckBox("Enable Status GUI (Pill Widget)")
        self.chk_gui_enable.setChecked(self.config_data.get("status_gui_enabled", True))
        self.chk_gui_enable.setStyleSheet("color: white;")
        self.chk_gui_enable.toggled.connect(self.on_gui_enable_toggled)
        layout.addRow("", self.chk_gui_enable)
        
        # Window Opacity
        self.slider_gui_opacity = self._create_slider(10, 100, self.config_data.get("status_gui_opacity", 1.0)*100)
        self.slider_gui_opacity.valueChanged.connect(self.on_gui_opacity_changed)
        layout.addRow(QLabel("Window Opacity:"), self.slider_gui_opacity)
        
        # Background Opacity (Alpha)
        self.slider_bg_opacity = self._create_slider(0, 255, self.config_data.get("status_gui_bg_opacity", 180))
        self.slider_bg_opacity.valueChanged.connect(self.on_bg_opacity_changed)
        layout.addRow(QLabel("Background Opacity:"), self.slider_bg_opacity)
        
        # Background Color & Transparency
        color_layout = QHBoxLayout()
        self.btn_bg_color = QPushButton("Choose Color")
        self.curr_bg_color = self.config_data.get("status_gui_color", "#000000")
        self.btn_bg_color.setStyleSheet(f"background: {self.curr_bg_color}; color: {'#fff' if self.curr_bg_color == '#000000' else '#000'}; border: 1px solid #555;")
        self.btn_bg_color.clicked.connect(self.pick_bg_color)
        
        self.chk_transparency = QCheckBox("Enable Transparency")
        self.chk_transparency.setChecked(self.config_data.get("status_gui_transparency", True))
        self.chk_transparency.setStyleSheet("color: white;")
        self.chk_transparency.toggled.connect(self.on_style_changed)
        
        self.chk_invisible = QCheckBox("Invisible Background")
        self.chk_invisible.setChecked(self.config_data.get("status_gui_invisible", False))
        self.chk_invisible.setStyleSheet("color: white;")
        self.chk_invisible.toggled.connect(self.on_invisible_toggled)
        
        color_layout.addWidget(self.btn_bg_color)
        color_layout.addWidget(self.chk_transparency)
        color_layout.addWidget(self.chk_invisible)
        layout.addRow("Widget Style:", color_layout)

        # Widget Lock Checkbox
        self.chk_lock_widget = QCheckBox("Lock Taskbar Widget Position")
        self.chk_lock_widget.setChecked(self.widget_config.get("locked", False))
        self.chk_lock_widget.setStyleSheet("color: white;")
        self.chk_lock_widget.toggled.connect(self.on_lock_toggled)
        layout.addRow("", self.chk_lock_widget)
        
        # Screenshot Location
        screenshot_layout = QHBoxLayout()
        self.input_screenshot = QLineEdit()
        self.input_screenshot.setReadOnly(True)
        self.input_screenshot.setText(self.config_data.get("screenshot_path", ""))
        self.input_screenshot.setPlaceholderText("Default: Pictures/Screenshots")
        self.input_screenshot.setStyleSheet("padding: 8px; background: #252526; border: 1px solid #555; color: #fff;")
        
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_screenshot_path)
        
        screenshot_layout.addWidget(self.input_screenshot)
        screenshot_layout.addWidget(btn_browse)
        layout.addRow("Screenshot Path:", screenshot_layout)

    def on_gui_enable_toggled(self, checked):
        if self.status_window:
            self.status_window.set_gui_visible(checked)

    def on_gui_opacity_changed(self, value):
        if self.status_window:
            self.status_window.set_gui_opacity(value / 100.0)

    def on_name_changed(self, text):
        self.config_data["name"] = text
        self.save_settings(silent=True)
        if self.status_window and hasattr(self.status_window, 'action_queue') and self.status_window.action_queue:
            self.status_window.action_queue.put(("UPDATE_NAME", text))
        
    def on_theme_changed(self, theme_name):
        self.config_data["theme"] = theme_name
        self.save_settings(silent=True)
        if self.status_window:
            self.status_window.set_theme(theme_name)

    def on_bg_opacity_changed(self, value):
        if self.status_window:
            self.status_window.set_bg_opacity(value)

    def on_invisible_toggled(self, checked):
        if self.status_window:
            self.status_window.set_invisible(checked)

    def pick_bg_color(self):
        color = QColorDialog.getColor(QColor(self.curr_bg_color), self, "Select Status GUI Background")
        if color.isValid():
            self.curr_bg_color = color.name()
            self.btn_bg_color.setStyleSheet(f"background: {self.curr_bg_color}; color: {'#fff' if self.curr_bg_color == '#000000' else '#000'}; border: 1px solid #555;")
            self.on_style_changed()

    def on_style_changed(self):
        if self.status_window:
            self.status_window.set_gui_style(self.curr_bg_color, self.chk_transparency.isChecked())

    def browse_screenshot_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Screenshot Storage Location")
        if path:
            self.input_screenshot.setText(path)

    def on_lock_toggled(self, checked):
        """Update StatusWindow live when checkbox is toggled."""
        if self.status_window:
            self.status_window.update_lock_state(checked)
        
        # Note: We can add immediate theme preview if desired, but restart is safer for now.

    def init_voice_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        self.tab_voice.setLayout(layout)
        
        # Rate Slider
        lbl_rate = QLabel("Speech Rate:")
        self.slider_rate = self._create_slider(50, 300, self.config_data.get("voice_rate", 175))
        layout.addWidget(lbl_rate)
        layout.addWidget(self.slider_rate)
        
        # Volume Slider
        lbl_vol = QLabel("Voice Volume:")
        # Slider is int 0-100, mapped to float 0.0-1.0
        current_vol = int(self.config_data.get("voice_volume", 1.0) * 100)
        self.slider_vol = self._create_slider(0, 100, current_vol)
        layout.addWidget(lbl_vol)
        layout.addWidget(self.slider_vol)
        
        # Test Button
        btn_test = QPushButton("🔊 Test Voice")
        btn_test.clicked.connect(self.test_voice)
        layout.addWidget(btn_test)
        
        layout.addStretch()

    def _create_slider(self, min_val, max_val, current_val):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(int(current_val))
        
        # We need the accent color here too
        current_theme = self.config_data.get("theme", "Neon Green")
        from .styles import THEME_COLORS
        accent = THEME_COLORS.get(current_theme, "#39FF14")
        
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid #444;
                height: 8px;
                background: #1e1e1e;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: 1px solid {accent};
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }}
        """)
        return slider

    def test_voice(self):
        """Play a test phrase using the CURRENT slider values, matching main engine logic."""
        rate = self.slider_rate.value()
        volume = self.slider_vol.value() / 100.0
        
        # Check for Piper Logic (Mirrors core/speaking.py)
        import platform
        import subprocess
        
        os_type = platform.system()
        piper_path = None
        model_path = None
        
        if os_type == 'Windows':
             piper_path = os.path.abspath("piper_engine/piper_windows/piper/piper.exe")
        else:
             piper_path = os.path.abspath("piper_engine/piper/piper")
        
        model_path = os.path.abspath("piper_engine/voice.onnx")
        
        use_piper = False
        if os.path.exists(piper_path) and os.path.exists(model_path):
             use_piper = True
             
        try:
            if use_piper:
                # Calculate Length Scale logic from speaking.py
                length_scale = 175.0 / max(50, rate)
                length_scale = max(0.5, min(2.0, length_scale))
                
                text = "This is a test of your voice settings."
                
                if os_type == 'Windows':
                    import pyaudio
                    import audioop
                    
                    piper_proc = subprocess.Popen(
                        [piper_path, '--model', model_path, '--output_raw', '--length_scale', str(length_scale)], 
                        stdin=subprocess.PIPE, 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL
                    )

                    p = pyaudio.PyAudio()
                    stream = p.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True)

                    piper_proc.stdin.write(text.encode('utf-8'))
                    piper_proc.stdin.close()

                    chunk_size = 1024
                    while True:
                        data = piper_proc.stdout.read(chunk_size)
                        if not data: break
                        
                        # Apply Volume
                        if volume != 1.0:
                            try:
                                data = audioop.mul(data, 2, volume)
                            except: pass
                            
                        stream.write(data)
                    
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    piper_proc.wait()
                    
                else:
                    QMessageBox.information(self, "Linux/Mac", "Piper test preview not fully implemented for this OS in Settings yet. Save to test.")

            else:
                # Pyttsx3 Fallback
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', rate)
                engine.setProperty('volume', volume)
                
                # Select voice based on OS
                if os.name == 'nt': # Windows
                    voices = engine.getProperty('voices')
                    for voice in voices:
                        if 'zira' in voice.name.lower() or 'david' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
                elif os.name == 'posix': # Mac/Linux
                     voices = engine.getProperty('voices')
                     for voice in voices:
                        if 'samantha' in voice.name.lower() or 'alex' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
                
                engine.say("This is a test of your voice settings.")
                engine.runAndWait()
                del engine
                
        except Exception as e:
            QMessageBox.warning(self, "Test Failed", f"Could not test voice: {e}")

    def reset_defaults(self):
        reply = QMessageBox.question(
            self, 'Reset Defaults', 
            'Are you sure you want to reset all settings to default?', 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.input_name.setText("Sir")
            index = self.combo_theme.findText("Neon Green")
            if index >= 0: self.combo_theme.setCurrentIndex(index)
            self.slider_rate.setValue(175)
            self.slider_vol.setValue(100)
            
            # Reset new GUI settings
            self.chk_gui_enable.setChecked(True)
            self.slider_gui_opacity.setValue(100)
            self.slider_bg_opacity.setValue(180)
            self.curr_bg_color = "#000000"
            self.btn_bg_color.setStyleSheet(f"background: {self.curr_bg_color}; color: #fff; border: 1px solid #555;")
            self.chk_transparency.setChecked(True)
            self.chk_lock_widget.setChecked(False)
            self.input_screenshot.setText("")

            self.save_settings(silent=True)

    def save_settings(self, silent=False):
        # Update config data
        self.config_data["name"] = self.input_name.text().strip()
        self.config_data["theme"] = self.combo_theme.currentText()
        self.config_data["voice_rate"] = self.slider_rate.value()
        self.config_data["voice_volume"] = self.slider_vol.value() / 100.0
        
        # New General Settings
        self.config_data["status_gui_enabled"] = self.chk_gui_enable.isChecked()
        self.config_data["status_gui_opacity"] = self.slider_gui_opacity.value() / 100.0
        self.config_data["status_gui_bg_opacity"] = self.slider_bg_opacity.value()
        self.config_data["status_gui_color"] = self.curr_bg_color
        self.config_data["status_gui_transparency"] = self.chk_transparency.isChecked()
        self.config_data["status_gui_invisible"] = self.chk_invisible.isChecked()
        self.config_data["screenshot_path"] = self.input_screenshot.text()
        
        # Save Taskbar Widget Config
        self.widget_config["locked"] = self.chk_lock_widget.isChecked()
        try:
             with open(self.widget_config_path, 'w') as f:
                json.dump(self.widget_config, f, indent=4)
             # Also ensure StatusWindow is updated on save (redundant but safe)
             if self.status_window:
                 self.status_window.update_lock_state(self.chk_lock_widget.isChecked())
        except Exception as e:
            print(f"[Settings] Error saving widget config: {e}")

        # Save to file
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config_data, f, indent=4)
            
            if not silent:
                QMessageBox.information(self, "Success", "Settings saved successfully.")
                self.close()
                
        except Exception as e:
            if not silent:
                QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
            else:
                print(f"[UI] Silent save error: {e}")

    def trigger_restart(self):
        if self.reset_event:
            print("[UI] Signaling restart from Settings...")
            self.reset_event.set()
        else:
            self.close()
