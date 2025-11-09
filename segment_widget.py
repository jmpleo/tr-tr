from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel

from styles import (
    TIMESTAMP_LABEL,
    SEGMENT_WIDGET
)


class SegmentWidget(QWidget):
    def __init__(self, start, end, text, translations):
        super().__init__()
        self.setup_ui(start, end, text, translations)

    def setup_ui(self, start, end, text, translations):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        timestamp_label = QLabel(f"[{start:.2f}s - {end:.2f}s]")
        timestamp_label.setStyleSheet(TIMESTAMP_LABEL)
        layout.addWidget(timestamp_label)

        if text:
            text_label = QLabel(f"Речь: {text}")
            text_label.setWordWrap(True)
            text_label.setStyleSheet("margin: 5px 0px;")
            layout.addWidget(text_label)

        for target_lang, translated_text in translations.items():
            translation_label = QLabel(f"Перевод ({target_lang}): {translated_text}")
            translation_label.setWordWrap(True)
            translation_label.setStyleSheet("margin: 5px 0px; color: #2c5aa0;")
            layout.addWidget(translation_label)

        self.setLayout(layout)
        self.setStyleSheet(SEGMENT_WIDGET)
