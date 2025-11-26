import os
from PyQt6.QtWidgets import (
    QApplication, QFileDialog,
    QVBoxLayout, QHBoxLayout, QSplitter,
    QWidget, QPushButton, QCheckBox, QLabel, QProgressBar,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QMutex, QWaitCondition
from utils import format_seconds


from styles import (
    STATUS_LABEL_ERROR,
    STATUS_LABEL_WARNING,
    STATUS_LABEL_READY,
    STATUS_LABEL_SUCCESS,
    RESULTS_TEXT,
    EXPORT_BUTTON,
    AUDIO_PATH_LABEL,
    LOGO_LABEL,
    DESC_LABEL,
    SECTION_LABEL,
    CANCEL_BUTTON,
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


class SpeechRecognitionWidget(QWidget):
    def __init__(self, transcribe_model, translation, save_dir):
        super().__init__()
        self.transcribe_model = transcribe_model
        self.translation = translation
        self.save_dir = save_dir
        self.processing_thread = None
        self.audio_file_path = None

        self.segment_queue = []
        self.segment_mutex = QMutex()
        self.segment_condition = QWaitCondition()
        self.processing_segment = False

        self.setup_ui()

        self.segment_timer = self.startTimer(10)


    def timerEvent(self, event):
        if self.segment_queue and not self.processing_segment:
            self.process_next_segment()

    def process_next_segment(self):
        self.segment_mutex.lock()
        try:
            if self.segment_queue:
                self.processing_segment = True
                segment_data = self.segment_queue.pop(0)
                self._add_segment_sync(*segment_data)
        finally:
            self.segment_mutex.unlock()

    def _add_segment_sync(self, start, end, text, translations):
        current_text = self.results_text.toHtml()
        b = format_seconds(start)
        e = format_seconds(end)

        self.results_text.setHtml(
            current_text
            + f'<hr/><b>[{b} - {e}]</b><p>{text}</p>'
            + ''.join(
                f"<p><b>({lang})</b> {translation}</p>"
                for lang, translation in translations.items()
            )
        )

        self.processing_segment = False

    def setup_ui(self):
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        tab_layout = QVBoxLayout(self)
        tab_layout.addWidget(main_splitter)

        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_panel.setStyleSheet(LEFT_PANEL)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([300, 900])

        app_title = QLabel("Полиглот")
        app_title.setStyleSheet(LOGO_LABEL)
        left_layout.addWidget(app_title)

        upload_card = QWidget()
        upload_card.setStyleSheet(UPLOAD_CARD)
        upload_layout = QVBoxLayout(upload_card)

        upload_title = QLabel("Аудио:")
        upload_title.setStyleSheet(SECTION_LABEL)
        upload_layout.addWidget(upload_title)

        upload_title_description = QLabel("Поддержка 99 языков")
        upload_title_description.setStyleSheet(DESC_LABEL)
        upload_title_description.setWordWrap(True)
        #upload_layout.addWidget(upload_title_description)

        self.select_audio_btn = QPushButton("Выбрать файл")
        self.select_audio_btn.clicked.connect(self.select_audio_file)
        self.select_audio_btn.setStyleSheet(SELECT_AUDIO_BUTTON)
        self.select_audio_btn.setToolTip("Поддерживаются 99 языков")
        upload_layout.addWidget(self.select_audio_btn)

        left_layout.addWidget(upload_card)
        left_layout.addSpacing(5)

        settings_card = QWidget()
        settings_card.setStyleSheet(SETTINGS_CARD)
        settings_layout = QVBoxLayout(settings_card)

        settings_title = QLabel("Дополнительно переводить на")
        settings_title.setStyleSheet(SECTION_LABEL)
        settings_layout.addWidget(settings_title)

        settings_title_description = QLabel("Языки: he, ar")
        settings_title_description.setStyleSheet(DESC_LABEL)
        settings_title_description.setWordWrap(True)
        #settings_layout.addWidget(settings_title_description)

        self.translate_en = QCheckBox("Английский")
        self.translate_ru = QCheckBox("Русский")
        self.translate_en_ru = QCheckBox("Русский (с Английского)")

        self.translate_en.setChecked(True)

        for checkbox in [self.translate_en, self.translate_ru, self.translate_en_ru]:
            checkbox.setStyleSheet(CHECKBOX)
            settings_layout.addWidget(checkbox)

        left_layout.addWidget(settings_card)
        left_layout.addSpacing(5)

        process_buttons_widget = QWidget()
        process_buttons_layout = QHBoxLayout(process_buttons_widget)
        process_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.process_btn = QPushButton("Начать распознавание")
        self.process_btn.clicked.connect(self.process_audio)
        self.process_btn.setStyleSheet(PROCESS_BUTTON)

        self.cancel_btn = QPushButton("Стоп")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setStyleSheet(CANCEL_BUTTON)
        self.cancel_btn.setEnabled(False)

        process_buttons_layout.addWidget(self.process_btn)
        process_buttons_layout.addWidget(self.cancel_btn)

        left_layout.addWidget(process_buttons_widget)

        progress_card = QWidget()
        progress_card.setStyleSheet(PROGRESS_CARD)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setStyleSheet(PROGRESS_BAR)
        self.progress_bar.setHidden(True)

        results_header = QWidget()
        results_header_layout = QHBoxLayout(results_header)

        self.audio_path_label = QLabel("Файл не выбран")
        self.audio_path_label.setStyleSheet(AUDIO_PATH_LABEL)

        export_widget = QWidget()
        export_layout = QHBoxLayout(export_widget)
        export_layout.setContentsMargins(0, 0, 0, 0)

        self.edit_btn = QPushButton("Изменить")
        self.edit_btn.clicked.connect(self.edit_result_text)
        self.copy_btn = QPushButton("Копировать")
        self.copy_btn.clicked.connect(self.copy_results)
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_results)

        for btn in [self.edit_btn, self.copy_btn, self.save_btn]:
            btn.setStyleSheet(EXPORT_BUTTON)
            export_layout.addWidget(btn)

        results_header_layout.addWidget(self.audio_path_label)
        results_header_layout.addStretch()
        results_header_layout.addWidget(export_widget)

        right_layout.addWidget(results_header)

        self.results_text = QTextEdit()
        #self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet(RESULTS_TEXT)

        right_layout.addWidget(self.results_text)

        self.status_label = QLabel("Выберите аудиофайл для начала работы")
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(self.progress_bar)

        self.update_ui_state()

    def edit_result_text(self):
        if self.results_text.isReadOnly():
            self.edit_btn.setText("Отменить редактирование")
            self.copy_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.process_btn.setEnabled(False)
            self.select_audio_btn.setEnabled(False)
            self.results_text.setReadOnly(False)
        else:
            self.edit_btn.setText("Изменить")
            self.copy_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.process_btn.setEnabled(True)
            self.select_audio_btn.setEnabled(True)
            self.results_text.setReadOnly(True)

    def update_ui_state(self):
        has_audio = self.audio_file_path is not None
        has_results = len(self.results_text.toPlainText()) > 0
        is_processing = self.processing_thread is not None and self.processing_thread.isRunning()
        self.progress_bar.setHidden(not is_processing)
        self.status_label.setHidden(not is_processing and not has_results)
        self.process_btn.setEnabled(has_audio and not is_processing)
        self.cancel_btn.setEnabled(is_processing)
        self.copy_btn.setEnabled(has_results and not is_processing)
        self.save_btn.setEnabled(has_results and not is_processing)
        self.edit_btn.setEnabled(has_results and not is_processing)
        self.select_audio_btn.setEnabled(not is_processing)
        self.translate_en.setEnabled(not is_processing)
        self.translate_ru.setEnabled(not is_processing)

    def select_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите аудио файл",
            "",
            "Audio Files (*.mp3 *.wav *.m4a *.ogg *.flac *.mp4);;All Files (*)"
        )

        if file_path:
            self.audio_file_path = file_path
            self.audio_path_label.setText(os.path.basename(file_path))
            self.status_label.setStyleSheet(STATUS_LABEL_READY)
            self.status_label.setText(f"Выбран файл: {file_path}")
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
            target_langs.append("-en")
        if self.translate_ru.isChecked():
            target_langs.append("-ru")
        if self.translate_en_ru.isChecked():
            target_langs.append("-en-ru")

        self.clear_results()
        self.status_label.setStyleSheet(STATUS_LABEL_READY)
        self.status_label.setText("Начало обработки аудио...")

        self.processing_thread = ProcessingThread(
            self.audio_file_path,
            target_langs,
            self.transcribe_model,
            self.save_dir,
            self.translation
        )

        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.segment_processed.connect(self.queue_segment)
        self.processing_thread.finished_processing.connect(self.processing_finished)
        self.processing_thread.error_occurred.connect(self.processing_error)
        self.processing_thread.start()

        self.update_ui_state()

    def queue_segment(self, start, end, text, translations):
        self.segment_mutex.lock()
        try:
            self.segment_queue.append((start, end, text, translations))
        finally:
            self.segment_mutex.unlock()

    def cancel_processing(self):
        if self.processing_thread and self.processing_thread.isRunning():
            self.status_label.setStyleSheet(STATUS_LABEL_WARNING)
            self.status_label.setText("Останавливается...")
            self.processing_thread.stop()

            self.segment_mutex.lock()
            try:
                self.segment_queue.clear()
                self.processing_segment = False
            finally:
                self.segment_mutex.unlock()

            self.status_label.setStyleSheet(STATUS_LABEL_WARNING)
            self.status_label.setText("Процесс остановлен пользователем")
            self.update_ui_state()

    def update_progress(self, message):
        self.status_label.setStyleSheet(STATUS_LABEL_READY)
        self.status_label.setText(message)

    def processing_finished(self, segments, txt_filename):
        if segments:
            self.status_label.setStyleSheet(STATUS_LABEL_SUCCESS)
            self.status_label.setText(f"Обработка завершена. Результаты сохранены в: {txt_filename}")

        self.update_ui_state()

    def processing_error(self, error_message):
        self.process_btn.setEnabled(True)
        self.status_label.setStyleSheet(STATUS_LABEL_ERROR)
        self.status_label.setText(f"Ошибка: {error_message}")
        QMessageBox.critical(self, "Ошибка", f"Во время обработки произошла ошибка:\n{error_message}")

        self.segment_mutex.lock()
        try:
            self.segment_queue.clear()
            self.processing_segment = False
        finally:
            self.segment_mutex.unlock()

        self.update_ui_state()

    def clear_results(self):
        self.results_text.clear()

        self.segment_mutex.lock()
        try:
            self.segment_queue.clear()
            self.processing_segment = False
        finally:
            self.segment_mutex.unlock()

        self.update_ui_state()

    def copy_results(self):
        text = self.results_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setStyleSheet(STATUS_LABEL_SUCCESS)
            self.status_label.setText("Текст скопирован в буфер обмена")
        else:
            self.status_label.setStyleSheet(STATUS_LABEL_WARNING)
            self.status_label.setText("Нет текста для копирования")

    def save_results(self):
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
                self.status_label.setStyleSheet(STATUS_LABEL_SUCCESS)
                self.status_label.setText(f"Результаты сохранены в: {file_path}")
            except Exception as e:
                self.status_label.setStyleSheet(STATUS_LABEL_ERROR)
                self.status_label.setText(f"Не удалось сохранить файл")
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
