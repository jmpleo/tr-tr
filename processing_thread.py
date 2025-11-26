import os
import logging
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from utils import format_seconds


class ProcessingThread(QThread):
    progress_updated = pyqtSignal(str)
    segment_processed = pyqtSignal(float, float, str, dict)
    finished_processing = pyqtSignal(list, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, audio_file, target_langs, transcribe_model, save_dir, translation):
        super().__init__()
        self.audio_file = audio_file
        self.target_langs = target_langs
        self.transcribe_model = transcribe_model
        self.save_dir = save_dir
        self.segments = []
        self.translation = translation
        self._is_running = True

    def isRunning(self):
        return self._is_running

    def run(self):
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                self.error_occurred.emit(f"Аудио файл недоступен: {self.audio_file}")
                return

            if not self._is_running:
                return

            self.progress_updated.emit("Распознавание языка...")
            logging.info("Распознавание языка...")

            segments, info = self.transcribe_model.transcribe(self.audio_file)
            detected_language = info.language if hasattr(info, 'language') else None

            if not self._is_running:
                return

            self.progress_updated.emit(f"Распознан язык '{detected_language}'")
            logging.info(f"Распознан язык '{detected_language}'")

            translate_model_seq = {}
            for target_lang in self.target_langs:
                if not self._is_running:
                    return

                langs = detected_language + target_lang
                langs_seq = langs.split('-')

                if len(langs_seq) < 2:
                    continue

                model_seq = []
                for i in range(len(langs_seq) - 1):
                    left = langs_seq[i]
                    right = langs_seq[i + 1]

                    self.progress_updated.emit(
                        f"Загрузка переводчика с '{left}' на '{right}'..."
                    )
                    logging.info(f"Загрузка переводчика с '{left}' на '{right}'...")
                    model = self.translation.load_translation_model(left, right)

                    if model is None:
                        model_seq = []
                        break

                    model_seq.append(model)

                if model_seq:
                    translate_model_seq[langs] = model_seq

            if not self._is_running:
                return

            self.progress_updated.emit("Сегментация...")

            for i, segment in enumerate(segments):
                if not self._is_running:
                    return

                self.progress_updated.emit(f"Преобразование сегмента {i+1}...")

                text = segment.text.strip() if segment.text else ""
                translations = {}

                for langs, model_seq in translate_model_seq.items():
                    if not self._is_running:
                        break

                    self.progress_updated.emit(f"({langs}) Перевод сегмента {i+1}...")
                    translated_text = [text]
                    try:
                        for model in model_seq:
                            translated_text = model.translate(translated_text)
                        translations[langs] = '\n'.join(translated_text)
                    except Exception as e:
                        logging.error(f"Translation failed: {e}")
                        translations[target_lang] = "Ошибка перевода"

                segment_data = (segment.start, segment.end, text, translations)
                self.segments.append(segment_data)
                self.segment_processed.emit(segment.start, segment.end, text, translations)

                if not self._is_running:
                    break

                checkpoint = self.save_results(checkpoint=True)
                self.progress_updated.emit(f"Обработаные сегменты сохранены в {checkpoint}...")

            if self._is_running:
                txt_filename = self.save_results()
                self._is_running = False
                self.finished_processing.emit(self.segments, txt_filename)

        except Exception as e:
            logging.error(f"Processing failed: {e}")
            self.error_occurred.emit(str(e))

    def stop(self):
        self._is_running = False

    def save_results(self, checkpoint=False):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        name = os.path.basename(self.audio_file).replace('.', '_')
        name = f'.{name}.txt' if checkpoint else f'{name}_{timestamp}.txt'

        filename = os.path.join(self.save_dir, name)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if not self.segments:
                    f.write("Речь в аудио не распознана\n")
                    return filename

                for start, end, text, translations in self.segments:
                    f.write(f"[{format_seconds(start)} - {format_seconds(end)}\n")
                    f.write(f"{text}\n")
                    if translations:
                        for target_lang, text_t in translations.items():
                            f.write(f"({target_lang}) {text_t}\n")
                    f.write("-" * 40 + "\n")

            if not checkpoint:
                logging.info(f"Results saved to: {filename}")

            return filename
        except Exception as e:
            logging.error(f"Failed to save file: {e}")
            return None