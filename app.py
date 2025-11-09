import sys
import logging
from PyQt6.QtWidgets import QApplication
from faster_whisper import WhisperModel

from translation import Translation
from speech_recognition_app import SpeechRecognitionApp


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    try:
        app = QApplication(sys.argv)
        window = SpeechRecognitionApp(
            transcribe_model=WhisperModel(
                model_size_or_path='./repo/Systran/faster-whisper-small',
                device="cpu",
                cpu_threads=3,
                local_files_only=True
            ),
            translation=Translation(translate_model_paths={
                ('he', 'en'): './repo/Helsinki-NLP/opus-mt-tc-big-he-en',
                ('he', 'ru'): './repo/Helsinki-NLP/opus-mt-he-ru',
                ('ar', 'en'): './repo/Helsinki-NLP/opus-mt-tc-big-ar-en',
                ('ar', 'ru'): './repo/Helsinki-NLP/opus-mt-ar-ru',
            }))
        logging.info("Transcription model loaded successfully")
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"Failed to load transcription model: {e}")
        sys.exit(1)


