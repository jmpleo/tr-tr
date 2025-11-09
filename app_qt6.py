import sys
import os
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QVBoxLayout, QHBoxLayout, QSplitter,
    QWidget, QPushButton, QCheckBox, QLabel, QProgressBar,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QTextCursor

from faster_whisper import WhisperModel
from transformers import pipeline


class ProcessingThread(QThread):
    progress_updated = pyqtSignal(int, str)
    segment_processed = pyqtSignal(float, float, str, dict)
    finished_processing = pyqtSignal(list, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, audio_file, target_langs, transcribe_model, save_dir):
        super().__init__()
        self.audio_file = audio_file
        self.target_langs = target_langs
        self.transcribe_model = transcribe_model
        self.save_dir = save_dir
        self.segments = []

    def run(self):
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                self.error_occurred.emit(f"Аудио файл недоступен: {self.audio_file}")
                return

            self.progress_updated.emit(5, "Начало обработки...")

            segments, info = self.transcribe_model.transcribe(self.audio_file)
            detected_language = info.language if hasattr(info, 'language') else None

            self.progress_updated.emit(15, f"Распознавание с '{detected_language}'...")

            translate_models = {}
            if self.target_langs:
                for target_lang in self.target_langs:
                    if (detected_language, target_lang) in self.transcribe_model.translate_model_paths:
                        model = load_translation_model(detected_language, target_lang)
                        if model:
                            translate_models[target_lang] = model
                            self.progress_updated.emit(25, f"Загрузка переводчика {detected_language}-{target_lang}...")

            for i, segment in enumerate(segments):
                self.progress_updated.emit(50, f"Обработка сегмента {i+1}...")

                text = segment.text.strip() if segment.text else ""
                translations = {}

                for target_lang, translate_model in translate_models.items():
                    try:
                        translated_text = translate_model(text)[0]['translation_text']
                        translations[target_lang] = translated_text
                    except Exception as e:
                        logging.error(f"Translation failed: {e}")
                        translations[target_lang] = "Ошибка перевода"

                segment_data = (segment.start, segment.end, text, translations)
                self.segments.append(segment_data)
                self.segment_processed.emit(segment.start, segment.end, text, translations)

            self.progress_updated.emit(95, "Сохранение результатов...")
            txt_filename = self.save_results()

            self.progress_updated.emit(100, "Завершено")
            self.finished_processing.emit(self.segments, txt_filename)

        except Exception as e:
            logging.error(f"Processing failed: {e}")
            self.error_occurred.emit(str(e))

    def save_results(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = os.path.join(self.save_dir, f"transcription_{timestamp}.txt")

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if not self.segments:
                    f.write("Речь в аудио не распознана\n")
                    return filename

                for start, end, text, translations in self.segments:
                    f.write(f"[{start:.2f}s - {end:.2f}s]\n")
                    f.write(f"Речь: {text}\n")
                    for target_lang, text_t in translations.items():
                        f.write(f"Перевод ({target_lang}): {text_t}\n")
                    f.write("-" * 40 + "\n")

            logging.info(f"Results saved to: {filename}")
            return filename
        except Exception as e:
            logging.error(f"Failed to save file: {e}")
            return None


class SegmentWidget(QWidget):
    def __init__(self, start, end, text, translations):
        super().__init__()
        self.setup_ui(start, end, text, translations)

    def setup_ui(self, start, end, text, translations):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        timestamp_label = QLabel(f"[{start:.2f}s - {end:.2f}s]")
        timestamp_label.setStyleSheet("color: #6c757d; font-size: 12px;")
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
        self.setStyleSheet("""
            SegmentWidget {
                border: 1px solid #e4e4e7;
                border-radius: 5px;
                margin: 5px 0px;
                background-color: white;
            }
        """)


class SpeechRecognitionApp(QMainWindow):
    def __init__(self, transcribe_model):
        super().__init__()
        self.transcribe_model = transcribe_model
        self.save_dir = os.path.join(os.path.expanduser("~"), 'tr-tr')
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        self.processing_thread = None
        self.audio_file_path = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("SpeechTranscribe")
        self.setMinimumSize(1200, 800)
        # Основной контейнер с разделением на панели
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)

        # ЛЕВАЯ ПАНЕЛЬ - НАСТРОЙКИ
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_panel.setStyleSheet("background-color: #f8f9fa; padding: 15px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Правая панель - результаты
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([300, 900])

        app_title = QLabel("SpeechTranscribe")
        app_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        app_title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        left_layout.addWidget(app_title)

        upload_card = QWidget()
        upload_card.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        upload_layout = QVBoxLayout(upload_card)

        upload_title = QLabel("Аудиофайл")
        upload_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        upload_layout.addWidget(upload_title)

        self.audio_path_label = QLabel("Файл не выбран")
        self.audio_path_label.setWordWrap(True)
        self.audio_path_label.setStyleSheet("color: #6c757d; font-size: 11px; margin: 5px 0;")
        upload_layout.addWidget(self.audio_path_label)

        self.select_audio_btn = QPushButton("Выбрать файл")
        self.select_audio_btn.clicked.connect(self.select_audio_file)
        self.select_audio_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                border: 1px dashed #adb5bd;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        upload_layout.addWidget(self.select_audio_btn)

        left_layout.addWidget(upload_card)
        left_layout.addSpacing(15)

        # Секция настроек перевода
        settings_card = QWidget()
        settings_card.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        settings_layout = QVBoxLayout(settings_card)

        settings_title = QLabel("Настройки перевода")
        settings_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        settings_layout.addWidget(settings_title)

        self.translate_en = QCheckBox("Английский")
        self.translate_ru = QCheckBox("Русский")

        for checkbox in [self.translate_en, self.translate_ru]:
            checkbox.setStyleSheet("margin: 5px 0;")
            settings_layout.addWidget(checkbox)

        left_layout.addWidget(settings_card)
        left_layout.addSpacing(15)

        # Кнопка обработки
        self.process_btn = QPushButton("Начать распознавание")
        self.process_btn.clicked.connect(self.process_audio)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        left_layout.addWidget(self.process_btn)

        # Прогресс
        progress_card = QWidget()
        progress_card.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin-top: 15px;
            }
        """)
        progress_layout = QVBoxLayout(progress_card)

        progress_title = QLabel("Прогресс")
        progress_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        progress_layout.addWidget(progress_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)

        self.progress_label = QLabel("Готов к работе")
        self.progress_label.setStyleSheet("font-size: 11px; color: #6c757d;")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        left_layout.addWidget(progress_card)

        # === ПРАВАЯ ПАНЕЛЬ: РЕЗУЛЬТАТЫ ===

        # Панель управления результатами
        results_header = QWidget()
        results_header_layout = QHBoxLayout(results_header)

        results_title = QLabel("Результаты распознавания")
        results_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        # Кнопки экспорта
        export_widget = QWidget()
        export_layout = QHBoxLayout(export_widget)
        export_layout.setContentsMargins(0, 0, 0, 0)

        self.copy_btn = QPushButton("📋 Копировать")
        self.copy_btn.clicked.connect(self.copy_results)
        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.save_results)

        for btn in [self.copy_btn, self.save_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
            """)
            export_layout.addWidget(btn)

        results_header_layout.addWidget(results_title)
        results_header_layout.addStretch()
        results_header_layout.addWidget(export_widget)

        right_layout.addWidget(results_header)

        # Область с результатами
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                line-height: 1.4;
            }
        """)

        right_layout.addWidget(self.results_text)

        # Статус бар
        self.status_label = QLabel("Выберите аудиофайл для начала работы")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #e7f3ff;
                color: #0066cc;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 11px;
                border-left: 3px solid #007bff;
            }
        """)
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
        # self.process_btn.setEnabled(False)
        self.set_interactive_elements_enabled(False)
        self.status_label.setText("Начало обработки аудио...")

        self.processing_thread = ProcessingThread(
            self.audio_file_path,
            target_langs,
            self.transcribe_model,
            self.save_dir
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

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        self.status_label.setText(message)

    def add_segment(self, start, end, text, translations):
        """Добавление сегмента в текстовое поле"""
        current_text = self.results_text.toPlainText()

        # Форматирование сегмента
        segment_text = f"[{start:.2f} - {end:.2f}] {text}\n"

        # Добавление переводов
        if translations:
            for lang, translation in translations.items():
                segment_text += f"({lang}) {translation}\n"

        segment_text += "\n"

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
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    color: #856404;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                }
            """)
        else:
            self.status_label.setText(f"Обработка завершена. Результаты сохранены в: {os.path.basename(txt_filename)}")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    color: #155724;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                    border-left: 3px solid #28a745;
                }
            """)

        self.update_ui_state()

    def processing_error(self, error_message):
        self.process_btn.setEnabled(True)
        self.progress_label.setText("Ошибка обработки")
        self.status_label.setText(f"Ошибка: {error_message}")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8d7da;
                color: #721c24;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 11px;
                border-left: 3px solid #dc3545;
            }
        """)
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

transcribe_model = None
translate_model_paths = {
    ('he', 'en'): './repo/Helsinki-NLP/opus-mt-tc-big-he-en',
    ('he', 'ru'): './repo/Helsinki-NLP/opus-mt-he-ru',
    ('ar', 'en'): './repo/Helsinki-NLP/opus-mt-tc-big-ar-en',
    ('ar', 'ru'): './repo/Helsinki-NLP/opus-mt-ar-ru',
}

translation_models = {}

def load_translation_model(from_lang, target_lang):
    if (from_lang, target_lang) in translation_models:
        return translation_models[from_lang, target_lang]
    try:
        if (from_lang, target_lang) in translate_model_paths:
            model_path = translate_model_paths[from_lang, target_lang]
            if not os.path.exists(model_path):
                logging.warning(f"Model path does not exist: {model_path}")
                return None

            model = pipeline("translation", model=model_path)
            translation_models[from_lang, target_lang] = model
            logging.info(f"Translation model for {from_lang}-{target_lang} loaded successfully")
            return model
        else:
            logging.warning(f"No translation model available for language: {from_lang}-{target_lang}")
            return None
    except Exception as e:
        logging.error(f"Failed to load translation model for {from_lang}-{target_lang}: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load transcription model
    try:
        transcribe_model = WhisperModel('./repo/Systran/faster-whisper-small')
        transcribe_model.translate_model_paths = translate_model_paths  # Attach for thread access
        logging.info("Transcription model loaded successfully")
    except Exception as e:
        logging.error(f"Failed to load transcription model: {e}")
        transcribe_model = None


    app = QApplication(sys.argv)
    #app.setStyle('Fusion')  # Modern style

    window = SpeechRecognitionApp(transcribe_model)
    window.show()

    sys.exit(app.exec())