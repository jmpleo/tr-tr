import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QTabWidget
from PyQt6.QtGui import QIcon
from utils import resource_path
from speech_recognition_widget import SpeechRecognitionWidget


class AppWindow(QMainWindow):
    def __init__(self, transcribe_model, translation):
        super().__init__()
        self.transcribe_model = transcribe_model
        self.translation = translation
        self.save_dir = os.path.join(os.path.expanduser("~"), 'tr-tr')
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Распознавание речи с автопереводом")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setMinimumSize(1200, 680)

        tab_widget = QTabWidget()
        self.setCentralWidget(tab_widget)

        speech_tab = SpeechRecognitionWidget(
            self.transcribe_model,
            self.translation,
            self.save_dir
        )
        tab_widget.addTab(speech_tab, "Распознавание речи")

        translate_tab = QWidget()
        tab_widget.addTab(translate_tab, "Переводчик")
