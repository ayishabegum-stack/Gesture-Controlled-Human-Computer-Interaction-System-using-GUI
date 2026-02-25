import sys
import subprocess
import threading
import pygame
import pyttsx3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QTextEdit, QFrame, QHBoxLayout, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer


class ControlWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧠 HCI Movement Control System")
        self.setGeometry(300, 100, 700, 600)
        self.setStyleSheet(self.load_styles())

        self.init_voice()
        self.init_sound()
        self.init_ui()

    def init_voice(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 160)
        self.engine.setProperty('volume', 0.9)

    def speak(self, text):
        threading.Thread(target=self._speak_text, args=(text,), daemon=True).start()

    def _speak_text(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def init_sound(self):
        pygame.mixer.init()
        self.click_sound = pygame.mixer.Sound("click.wav")

    def play_sound(self):
        self.click_sound.play()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)

        # Title
        title = QLabel("🌐 Gesture-Controlled Human-Computer Interface")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #00FF88;")
        main_layout.addWidget(divider)

        # Button Grid Layout
        button_layout = QGridLayout()
        button_layout.setSpacing(20)

        self.hand_btn = QPushButton("🖐️ Hand Gesture Control")
        self.eye_btn = QPushButton("👁️ Eye Gesture Control")

        self.hand_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.eye_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.hand_btn.clicked.connect(self.run_hand_control)
        self.eye_btn.clicked.connect(self.run_eye_control)

        button_layout.addWidget(self.hand_btn, 0, 0)
        button_layout.addWidget(self.eye_btn, 0, 1)

        main_layout.addLayout(button_layout)

        # Instruction Header
        instruction_header = QLabel("📘 Gesture Guide")
        instruction_header.setObjectName("sectionHeader")
        main_layout.addWidget(instruction_header)

        # Instructions Box
        self.instructions = QTextEdit()
        self.instructions.setReadOnly(True)
        self.instructions.setObjectName("instructionBox")
        self.instructions.setPlainText(
             "🔹 Hand Gestures:\n"
             "• Index Finger → Cursor Movement\n"
             "• Pinch (Thumb + Index) → Left Click\n"
             "• Hold Pinch (>1.2s) → Drag Mode\n"
             "• Release Pinch → Drop or Single Click\n"
             "• Middle Finger Up/Down → Scroll Up/Down\n"
             "• Thumb Up (others folded) → Volume Up\n"
             "• Thumb Down (others folded) → Volume Down\n"
             "• Open Palm (all fingers extended) → Exit Hand Control\n\n"
           "🔹 Eye Gestures:\n"
           "• Eye Movement → Cursor Movement\n"
           "• Single Blink → Left Click\n"
           "• Double Blink → Double Click\n"
           "• Right Eye Blink (hold) → volume Up\n"
           "• Left Eye Blink (hold) → volume Down\n"
           "• Open Mouth → Exit Eye Control"
        )
        main_layout.addWidget(self.instructions)

        # Bottom bar with status and exit button
        bottom_layout = QHBoxLayout()
        self.status_label = QLabel("🟢 Interface Ready. Awaiting Commands...")
        self.status_label.setObjectName("statusLabel")

        self.quit_btn = QPushButton("❌ Exit")
        self.quit_btn.clicked.connect(self.exit_app)
        self.quit_btn.setFixedWidth(100)

        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.quit_btn)

        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def load_styles(self):
        return """
        QWidget {
            background-color: #0f0f0f;
            color: #00ff99;
            font-family: 'Segoe UI', sans-serif;
        }
        #titleLabel {
            font-size: 24px;
            font-weight: bold;
            color: #00ff99;
            background-color: #1a1a1a;
            padding: 18px;
            border-radius: 12px;
        }
        #sectionHeader {
            font-size: 16px;
            color: #00ffcc;
            margin-top: 10px;
        }
        QPushButton {
            background-color: #1a1a1a;
            color: #00ff99;
            padding: 16px;
            font-size: 16px;
            border: 2px solid #00ff99;
            border-radius: 14px;
        }
        QPushButton:hover {
            background-color: #222;
            border-color: #00ffaa;
        }
        QPushButton:pressed {
            background-color: #111;
            border-color: #00ee88;
        }
        #statusLabel {
            font-size: 14px;
            font-weight: bold;
            color: #00ff66;
            padding: 6px;
        }
        #instructionBox {
            background-color: #1a1a1a;
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 10px;
            font-size: 13px;
        }
        """

    def run_hand_control(self):
        self.status_label.setText("🟡 Hand Gesture Control Activated...")
        self.play_sound()
        self.speak("Hand gesture control activated")
        subprocess.Popen(["python", "hand_control.py"])

    def run_eye_control(self):
        self.status_label.setText("🟡 Eye Gesture Control Activated...")
        self.play_sound()
        self.speak("Eye gesture control activated")
        subprocess.Popen(["python", "eye_control.py"])

    def exit_app(self):
        self.play_sound()
        self.speak("Exiting interface. Goodbye.")
        QTimer.singleShot(2500, QApplication.quit)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())              
