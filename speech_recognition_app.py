import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QVBoxLayout, QHBoxLayout, QSplitter,
    QWidget, QPushButton, QCheckBox, QLabel, QProgressBar,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor


from styles import (
    AUDIO_PATH_LABEL,
    STATUS_LABEL_ERROR,
    STATUS_LABEL_WARNING,
    STATUS_LABEL_READY,
    STATUS_LABEL_SUCCESS,
    RESULTS_TEXT,
    EXPORT_BUTTON,
    SECTION_LABEL,
    PROGRESS_LABEL,
    PROGRESS_BAR,
    PROGRESS_CARD,
    PROCESS_BUTTON,
    CHECKBOX,
    SETTINGS_CARD,
    SELECT_AUDIO_BUTTON,
    UPLOAD_CARD,
    LEFT_PANEL,
)
from processing_thread import ProcessingThread


class SpeechRecognitionApp(QMainWindow):
    def __init__(self, transcribe_model, translation):
        super().__init__()
        self.transcribe_model = transcribe_model
        self.translation = translation
        self.save_dir = os.path.join(os.path.expanduser("~"), 'tr-tr')
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        self.processing_thread = None
        self.audio_file_path = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("SpeechTranscribe")
        self.setMinimumSize(1200, 680)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)

        # ЛЕВАЯ ПАНЕЛЬ - НАСТРОЙКИ
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_panel.setStyleSheet(LEFT_PANEL)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Правая панель - результаты
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([300, 900])

        app_title = QLabel("Распознование речи")
        app_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        app_title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        left_layout.addWidget(app_title)

        upload_card = QWidget()
        upload_card.setStyleSheet(UPLOAD_CARD)
        upload_layout = QVBoxLayout(upload_card)

        #self.audio_label = QLabel("Аудио")
        #self.audio_label.setStyleSheet(SECTION_LABEL)
        #upload_layout.addWidget(self.audio_label)

        #self.audio_path_label = QLabel("Файл не выбран")
        #self.audio_path_label.setWordWrap(True)
        #self.audio_path_label.setStyleSheet(AUDIO_PATH_LABEL)
        #upload_layout.addWidget(self.audio_path_label)

        self.select_audio_btn = QPushButton("Выбрать файл")
        self.select_audio_btn.clicked.connect(self.select_audio_file)
        self.select_audio_btn.setStyleSheet(SELECT_AUDIO_BUTTON)
        upload_layout.addWidget(self.select_audio_btn)

        left_layout.addWidget(upload_card)
        left_layout.addSpacing(5)

        # Секция настроек перевода
        settings_card = QWidget()
        settings_card.setStyleSheet(SETTINGS_CARD)
        settings_layout = QVBoxLayout(settings_card)

        settings_title = QLabel("Дополнительно переводить на:")
        settings_title.setStyleSheet(SECTION_LABEL)
        settings_layout.addWidget(settings_title)

        self.translate_en = QCheckBox("Английский")
        self.translate_ru = QCheckBox("Русский")

        for checkbox in [self.translate_en, self.translate_ru]:
            checkbox.setStyleSheet(CHECKBOX)
            settings_layout.addWidget(checkbox)

        left_layout.addWidget(settings_card)
        left_layout.addSpacing(5)

        # Кнопка обработки
        self.process_btn = QPushButton("Начать распознавание")
        self.process_btn.clicked.connect(self.process_audio)
        self.process_btn.setStyleSheet(PROCESS_BUTTON)
        left_layout.addWidget(self.process_btn)

        # Прогресс
        progress_card = QWidget()
        progress_card.setStyleSheet(PROGRESS_CARD)
        progress_layout = QVBoxLayout(progress_card)

        progress_title = QLabel("Прогресс")
        progress_title.setStyleSheet(SECTION_LABEL)
        progress_layout.addWidget(progress_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(PROGRESS_BAR)

        self.progress_label = QLabel("Выберите файл")
        self.progress_label.setStyleSheet(PROGRESS_LABEL)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        left_layout.addWidget(progress_card)

        # Панель управления результатами
        results_header = QWidget()
        results_header_layout = QHBoxLayout(results_header)

        self.audio_path_label = QLabel("Файл не выбран")
        self.audio_path_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        #results_title = QLabel("Результаты распознавания")
        #results_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        # Кнопки экспорта
        export_widget = QWidget()
        export_layout = QHBoxLayout(export_widget)
        export_layout.setContentsMargins(0, 0, 0, 0)

        self.copy_btn = QPushButton("Копировать")
        self.copy_btn.clicked.connect(self.copy_results)
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_results)

        for btn in [self.copy_btn, self.save_btn]:
            btn.setStyleSheet(EXPORT_BUTTON)
            export_layout.addWidget(btn)

        #results_header_layout.addWidget(results_title)
        results_header_layout.addWidget(self.audio_path_label)
        results_header_layout.addStretch()
        results_header_layout.addWidget(export_widget)

        right_layout.addWidget(results_header)

        # Область с результатами
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet(RESULTS_TEXT)

        right_layout.addWidget(self.results_text)

        # Статус бар
        self.status_label = QLabel("Выберите аудиофайл для начала работы")
        self.status_label.setStyleSheet(STATUS_LABEL_READY)
        right_layout.addWidget(self.status_label)

        self.update_ui_state()

    def update_ui_state(self):
        has_audio = self.audio_file_path is not None
        has_results = len(self.results_text.toPlainText()) > 0

        self.process_btn.setEnabled(has_audio)
        self.copy_btn.setEnabled(has_results)
        self.save_btn.setEnabled(has_results)

    def select_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите аудио файл",
            "",
            "Audio Files (*.mp3 *.wav *.m4a *.ogg *.flac);;All Files (*)"
        )

        if file_path:
            self.audio_file_path = file_path
            self.audio_path_label.setText(os.path.basename(file_path))
            self.status_label.setText(f"Выбран файл: {os.path.basename(file_path)}")
            self.clear_results()
            self.update_ui_state()

    def process_audio(self):
        if not self.audio_file_path:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите аудио файл")
            return

        if self.transcribe_model is None:
            QMessageBox.critical(self, "Ошибка", "Модель транскрипции недоступна")
            return

        target_langs = []
        if self.translate_en.isChecked():
            target_langs.append("en")
        if self.translate_ru.isChecked():
            target_langs.append("ru")

        self.clear_results()
        self.set_interactive_elements_enabled(False)
        self.status_label.setText("Начало обработки аудио...")

        self.processing_thread = ProcessingThread(
            self.audio_file_path,
            target_langs,
            self.transcribe_model,
            self.save_dir,
            self.translation
        )

        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.segment_processed.connect(self.add_segment)
        self.processing_thread.finished_processing.connect(self.processing_finished)
        self.processing_thread.error_occurred.connect(self.processing_error)
        self.processing_thread.start()

    def set_interactive_elements_enabled(self, enabled):
        self.select_audio_btn.setEnabled(enabled)
        self.translate_en.setEnabled(enabled)
        self.translate_ru.setEnabled(enabled)
        self.process_btn.setEnabled(enabled)
        self.copy_btn.setEnabled(enabled and len(self.results_text.toPlainText()) > 0)
        self.save_btn.setEnabled(enabled and len(self.results_text.toPlainText()) > 0)

    def update_progress(self, value, message, step_message=""):
        self.progress_bar.setValue(value)
        self.progress_label.setText(step_message)
        self.status_label.setText(message)

    def add_segment(self, start, end, text, translations):
        """Добавление сегмента в текстовое поле"""
        current_text = self.results_text.toPlainText()

        # Форматирование сегмента
        segment_text = f"[{start:.2f} - {end:.2f}]\n"
        segment_text += f"{text}\n"
        segment_text += "Перевод:\n"
        # Добавление переводов
        if translations:
            for lang, translation in translations.items():
                segment_text += f"({lang}) {translation}\n"

        segment_text += "\n\n"

        # Добавление к существующему тексту
        new_text = current_text + segment_text
        self.results_text.setPlainText(new_text)

        # Прокрутка вниз
        cursor = self.results_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.results_text.setTextCursor(cursor)

    def processing_finished(self, segments, txt_filename):
        self.set_interactive_elements_enabled(True)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Обработка завершена")

        if not segments:
            self.status_label.setText("Речь в аудио не распознана")
            self.status_label.setStyleSheet(STATUS_LABEL_WARNING)
        else:
            self.status_label.setText(f"Обработка завершена. Результаты сохранены в: {os.path.basename(txt_filename)}")
            self.status_label.setStyleSheet(STATUS_LABEL_SUCCESS)

        self.update_ui_state()

    def processing_error(self, error_message):
        self.process_btn.setEnabled(True)
        self.progress_label.setText("Ошибка обработки")
        self.status_label.setText(f"Ошибка: {error_message}")
        self.status_label.setStyleSheet(STATUS_LABEL_ERROR)
        QMessageBox.critical(self, "Ошибка", f"Во время обработки произошла ошибка:\n{error_message}")
        self.update_ui_state()

    def clear_results(self):
        """Очистка результатов"""
        self.results_text.clear()
        self.update_ui_state()

    def copy_results(self):
        """Копирование результатов в буфер обмена"""
        text = self.results_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText("Текст скопирован в буфер обмена")
        else:
            self.status_label.setText("Нет текста для копирования")

    def save_results(self):
        """Сохранение результатов в файл"""
        text = self.results_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для сохранения")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты",
            os.path.join(self.save_dir, "transcription.txt"),
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.status_label.setText(f"Результаты сохранены в: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
