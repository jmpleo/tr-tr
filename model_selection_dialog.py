from utils import resource_path
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtGui import QIcon


class ModelSelectionDialog(QDialog):
    def __init__(self, available_transcribe_models, parent=None):
        super().__init__(parent)
        self.available_transcribe_models = available_transcribe_models
        self.selected_model = None
        self.provider = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Настройки")
        self.setFixedSize(400, 150)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        layout = QVBoxLayout()

        label = QLabel("Выберите модель распознования речи:")
        layout.addWidget(label)

        self.model_combo = QComboBox()
        for provider, models in self.available_transcribe_models.items():
            for name, model in models:
                self.model_combo.addItem(name, (provider, model))
        layout.addWidget(self.model_combo)

        button_layout = QHBoxLayout()

        self.ok_button = QPushButton("Да")
        self.ok_button.clicked.connect(self.accept_selection)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def accept_selection(self):
        provider, model_name = self.model_combo.currentData()
        self.selected_model = model_name
        self.provider = provider
        self.accept()

    def get_selected_model(self):
        return self.provider, self.selected_model