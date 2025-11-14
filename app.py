import sys
import os
import logging
from translation import Translation
from speech_recognition_window import SpeechRecognitionWindow
from model_selection_dialog import ModelSelectionDialog
from model_loader_thread import ModelLoaderThread, WhisperModel
from loading_dialog import LoadingDialog
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox


class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.model_dialog = ModelSelectionDialog(
            available_transcribe_models=self.available_transcribe_models()
        )
        self.repo_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'repo'
        )
        self.loading_dialog = LoadingDialog()
        self.window = None
        self.loader_thread = None

    @staticmethod
    def available_transcribe_models():
        return {
            "Systran": [
                ("tiny (~ 1.8 Гб)", "faster-whisper-tiny"),
                ("smallest (~ 2 Гб)", "faster-whisper-base"),
                ("small (~ 3 Гб)", "faster-whisper-small"),
                ("medium (~5 Гб)", "faster-whisper-medium"),
                ("large v2 (~8 Гб)", "faster-whisper-large-v2"),
                # ("large v3 (~9.1 Гб)", "faster-whisper-large-v3"),
            ]
        }

    @staticmethod
    def available_translate_models():
        return {
            ('he', 'en'): 'Helsinki-NLP/opus-mt-tc-big-he-en',
            ('he', 'ru'): 'Helsinki-NLP/opus-mt-he-ru',
            ('ar', 'en'): 'Helsinki-NLP/opus-mt-tc-big-ar-en',
            ('ar', 'ru'): 'Helsinki-NLP/opus-mt-ar-ru',
        }

    def run(self):
        if self.model_dialog.exec() == QDialog.DialogCode.Accepted:
            provider, selected_model = self.model_dialog.get_selected_model()
            logging.info(f"Selected model: {selected_model}")

            model_path = os.path.join(
                self.repo_dir,
                provider,
                selected_model
            )
            self.load_model(model_path)
            #self.on_model_loaded(None)
            self.app.exec()
        else:
            logging.info("Application cancelled by user")
            sys.exit(0)

    def load_model(self, model_path):
        #self.loading_dialog.show()
        #self.app.processEvents()
        model = WhisperModel(
            model_size_or_path=model_path,
            device='cpu',
            compute_type='float32',
            cpu_threads=3,
            local_files_only=True
        )
        if model:
            self.on_model_loaded(model)
        else:
            self.on_model_error("Не получилось загрузить модель")
        #self.loader_thread = ModelLoaderThread(model_path)
        #self.loader_thread.finished_signal.connect(self.on_model_loaded)
        #self.loader_thread.error_signal.connect(self.on_model_error)
        #self.loader_thread.start()

    def on_model_loaded(self, model):
        #self.loading_dialog.accept()
        #self.loader_thread.quit()
        translation = self.create_translation()
        self.window = SpeechRecognitionWindow(
            transcribe_model=model,
            translation=translation
        )
        self.window.show()

    def create_translation(self):
        return Translation(
            translate_model_paths=self.available_translate_models(),
            root_dir=self.repo_dir
        )

    def on_model_error(self, error_msg):
        QMessageBox.critical(
            None, "Error", f"Failed to load transcription model: {error_msg}"
        )
        sys.exit(1)
