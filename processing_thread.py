import os
import logging
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal, Qt


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

    def run(self):
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                self.error_occurred.emit(f"Аудио файл недоступен: {self.audio_file}")
                return

            self.progress_updated.emit("Распознование языка...")

            segments, info = self.transcribe_model.transcribe(self.audio_file)
            detected_language = info.language if hasattr(info, 'language') else None

            self.progress_updated.emit(f"Распознан язык '{detected_language}'")

            translate_models = {}
            if self.target_langs:
                for target_lang in self.target_langs:
                    self.progress_updated.emit(
                        f"Загрузка переводчика с '{detected_language}' на '{target_lang}'..."
                    )
                    model = self.translation.load_translation_model(detected_language, target_lang)
                    if model:
                        translate_models[target_lang] = model


            self.progress_updated.emit("Сегментация...")

            for i, segment in enumerate(segments):
                self.progress_updated.emit(f"Распознавание аудиосегмента {i+1}...")

                text = segment.text.strip() if segment.text else ""
                translations = {}

                for target_lang, translate_model in translate_models.items():
                    self.progress_updated.emit(f"Перевод аудиосегмента {i+1}...")
                    try:
                        translated_text = translate_model(text)[0]['translation_text']
                        translations[target_lang] = translated_text
                    except Exception as e:
                        logging.error(f"Translation failed: {e}")
                        translations[target_lang] = "Ошибка перевода"

                segment_data = (segment.start, segment.end, text, translations)
                self.segments.append(segment_data)
                self.segment_processed.emit(segment.start, segment.end, text, translations)
                checkpoint = self.save_results(checkpoint=True)
                self.progress_updated.emit(f"Обработаные сегменты сохранены в {checkpoint}...")


            self.progress_updated.emit("Сохранение...")
            txt_filename = self.save_results()

            self.progress_updated.emit("Выполнено")
            self.finished_processing.emit(self.segments, txt_filename)

        except Exception as e:
            logging.error(f"Processing failed: {e}")
            self.error_occurred.emit(str(e))

    def save_results(self, checkpoint=False):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        name = os.path.basename(self.audio_file).replace('.', '_')
        name = f'.{name}.{timestamp}' if checkpoint else f'{name}_{timestamp}.txt'
        filename = os.path.join(self.save_dir, name)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if not self.segments:
                    f.write("Речь в аудио не распознана\n")
                    return filename

                for start, end, text, translations in self.segments:
                    f.write(f"[{start:.2f}s - {end:.2f}s]\n")
                    f.write(f"{text}\n")
                    f.write("Перевод:\n")
                    for target_lang, text_t in translations.items():
                        f.write(f"({target_lang}) {text_t}\n")
                    f.write("-" * 40 + "\n")

            logging.info(f"Results saved to: {filename}")
            return filename
        except Exception as e:
            logging.error(f"Failed to save file: {e}")
            return None

