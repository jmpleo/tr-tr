# Основные стили для приложения
MAIN_WINDOW = """
    QMainWindow {
        background-color: #ffffff;
        color: #000000;
    }
"""

LEFT_PANEL = """
    QWidget {
        background-color: #f5f5f5;
        padding: 15px;
        border: none;
        color: #000000;
    }
"""

UPLOAD_CARD = """
    QWidget {
        background: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        color: #000000;
    }
"""

AUDIO_PATH_LABEL = """
    QLabel {
        color: #424242;
        font-size: 12px;
        margin: 5px 0;
        font-weight: bold;
        background: transparent;
        border: none;
    }
"""

SELECT_AUDIO_BUTTON = """
    QPushButton {
        background-color: #ffffff;
        border: 2px dashed #757575;
        padding: 8px;
        border-radius: 5px;
        color: #000000;
        font-weight: bold;
        min-height: 15px;
    }
    QPushButton:hover {
        background-color: #eeeeee;
        border: 2px dashed #424242;
    }
    QPushButton:pressed {
        background-color: #e0e0e0;
    }
"""

SETTINGS_CARD = """
    QWidget {
        background: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        color: #000000;
    }
"""

CHECKBOX = """
    QCheckBox {
        margin: 3px 0;
        color: #000000;
        background: transparent;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 2px solid #757575;
        border-radius: 3px;
        background: #ffffff;
    }
    QCheckBox::indicator:checked {
        background: #007bff;
        border: 2px solid #007bff;
    }
    QCheckBox::indicator:unchecked:hover {
        border: 2px solid #424242;
    }
"""





PROCESS_BUTTON = """
    QPushButton {
        background-color: #007bff;
        color: #ffffff;
        border: 2px solid #0056b3;
        padding: 12px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 6px;
        min-height: 15px;
    }
    QPushButton:hover {
        background-color: #0056b3;
        border: 2px solid #004085;
    }
    QPushButton:pressed {
        background-color: #004085;
    }
    QPushButton:disabled {
        background-color: #9e9e9e;
        border: 2px solid #757575;
        color: #616161;
    }
"""

PROGRESS_CARD = """
    QWidget {
        background: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-top: 15px;
        color: #000000;
    }
"""



PROGRESS_BAR = """
    QProgressBar {
        border: 2px solid #bdbdbd;
        border-radius: 4px;
        text-align: center;
        background: #ffffff;
        color: #000000;
        min-height: 5px;
        height: 10px;
    }
    QProgressBar::chunk {
        background-color: #007bff;
        border-radius: 2px;
        border: 1px solid #0056b3;
    }
"""

PROGRESS_LABEL = """
    QLabel {
        font-size: 12px;
        color: #424242;
        font-weight: bold;
        background: transparent;
        border: none;
    }
"""

SECTION_LABEL = """
    QLabel {
        font-size: 14px;
        color: #424242;
        font-weight: bold;
        background: transparent;
        padding: 0;
        border: none;
    }
"""

EXPORT_BUTTON = """
    QPushButton {
        background-color: #28a745;
        color: #ffffff;
        border: 2px solid #1e7e34;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        min-height: 15px;
    }
    QPushButton:hover {
        background-color: #218838;
        border: 2px solid #1c7430;
    }
    QPushButton:pressed {
        background-color: #1e7e34;
    }
    QPushButton:disabled {
        background-color: #9e9e9e;
        border: 2px solid #757575;
        color: #616161;
    }
"""

RESULTS_TEXT = """
    QTextEdit {
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
        line-height: 1.4;
        color: #000000;
        selection-background-color: #007bff;
    }
"""

STATUS_LABEL_READY = """
    QLabel {
        background-color: #e3f2fd;
        color: #0d47a1;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid #90caf9;
        border-left: 3px solid #1976d2;
    }
"""

STATUS_LABEL_SUCCESS = """
    QLabel {
        background-color: #e8f5e9;
        color: #1b5e20;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid #a5d6a7;
        border-left: 3px solid #388e3c;
    }
"""

STATUS_LABEL_WARNING = """
    QLabel {
        background-color: #fffde7;
        color: #f57f17;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid #fff59d;
        border-left: 3px solid #fbc02d;
    }
"""

STATUS_LABEL_ERROR = """
    QLabel {
        background-color: #ffebee;
        color: #b71c1c;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid #ef9a9a;
        border-left: 3px solid #d32f2f;
    }
"""

SEGMENT_WIDGET = """
    SegmentWidget {
        border: 2px solid #e0e0e0;
        border-radius: 5px;
        margin: 5px 0px;
        background-color: #ffffff;
    }
"""

TIMESTAMP_LABEL = """
    QLabel {
        color: #424242;
        font-size: 12px;
        font-weight: bold;
        background: transparent;
        border: none;
    }
"""

# Глобальные стили для отключения системной темы
GLOBAL_STYLES = """
    * {
        background-color: #ffffff;
        color: #000000;
        border: none;
        outline: none;
        font-family: 'Segoe UI', Arial, sans-serif;
    }

    QWidget:disabled {
        color: #616161;
    }

    QLineEdit {
        border: 2px solid #e0e0e0;
        border-radius: 4px;
        padding: 6px;
        background: #ffffff;
        color: #000000;
        font-size: 14px;
        min-height: 15px;
    }

    QLineEdit:focus {
        border: 2px solid #007bff;
    }

    QComboBox {
        border: 2px solid #e0e0e0;
        border-radius: 4px;
        padding: 6px;
        background: #ffffff;
        color: #000000;
        min-height: 15px;
        min-width: 80px;
    }

    QComboBox::drop-down {
        border: none;
        width: 20px;
    }

    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid #424242;
        width: 0px;
        height: 0px;
    }

    QComboBox QAbstractItemView {
        border: 2px solid #e0e0e0;
        background: #ffffff;
        color: #000000;
        selection-background-color: #007bff;
        selection-color: #ffffff;
    }

    QScrollBar:vertical {
        border: none;
        background: #f5f5f5;
        width: 12px;
        margin: 0px;
    }

    QScrollBar::handle:vertical {
        background: #bdbdbd;
        border-radius: 6px;
        min-height: 15px;
    }

    QScrollBar::handle:vertical:hover {
        background: #9e9e9e;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }
"""