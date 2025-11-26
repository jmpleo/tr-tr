import sys
import os
import logging
from faster_whisper import WhisperModel
from translation import Translation
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from app_window import AppWindow
from model_selection_dialog import ModelSelectionDialog
from loading_dialog import LoadingDialog
from utils import resource_path


class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.model_dialog = ModelSelectionDialog(self.available_transcribe_models())
        self.loading_dialog = LoadingDialog()
        self.window = None
        self.loader_thread = None

    def available_transcribe_models(self):
        models_meta = {
            "Systran": [
                ("tiny ~ 1.5 Гб - самый быстрый ", "faster-whisper-tiny"),
                ("smallest ~ 2 Гб - быстрый ", "faster-whisper-base"),
                ("small ~ 3 Гб - скорость + качество", "faster-whisper-small"),
                ("medium ~ 4 Гб - качество", "faster-whisper-medium"),
                ("large v2 ~ 5 Гб - лучшее качество ", "faster-whisper-large-v2")
            ]
        }
        return {
            provider: [
                (desc, os.path.join(resource_path('repo'), provider, name))
                for desc, name in models
                if name in os.listdir(os.path.join(resource_path('repo'), provider))
            ]
            for provider, models in models_meta.items()
        }

    def available_translate_models(self, provider='Helsinki-NLP'):
        model_paths = {}
        for m in os.listdir(os.path.join(resource_path('repo'), provider)):
            from_lang, to_lang = m.split('-', maxsplit=1)
            model_paths[(from_lang, to_lang)] = os.path.join(resource_path('repo'), provider, m)
        return model_paths

    def run(self):
        if self.model_dialog.exec() == QDialog.DialogCode.Accepted:
            provider, selected_model_path = self.model_dialog.get_selected_model()
            logging.info(f"Selected model: {provider}/{os.path.basename(selected_model_path)}")
            self.load_model(selected_model_path)
            #self.on_model_loaded(None)
            self.app.exec()
        else:
            logging.info("Application cancelled by user")
            sys.exit(0)

    def load_model(self, model_path):
        #self.loading_dialog.show()
        #self.app.processEvents()
        logging.info(f"load_model {model_path}...")

        if not os.path.exists(model_path):
            self.on_model_error(
                f"Отсутствует модель распознавания:\n{model_path}"
            )

        try:
            transcribe_model = WhisperModel(
                model_size_or_path=model_path,
                device='cpu',
                compute_type='float32',
                cpu_threads=3
            )

            self.on_model_loaded(transcribe_model)

        except Exception as e:
            self.on_model_error(
                f"Не получилось загрузить модель:\n{e}"
            )

        #self.loader_thread = ModelLoaderThread(model_path)
        #self.loader_thread.finished_signal.connect(self.on_model_loaded)
        #self.loader_thread.error_signal.connect(self.on_model_error)
        #self.loader_thread.start()

    def on_model_loaded(self, transcribe_model):
        translation = Translation(self.available_translate_models())
        self.window = AppWindow(transcribe_model, translation)
        self.window.show()

    def on_model_error(self, error_msg):
        QMessageBox.critical(None, "Ошибка", error_msg)
        sys.exit(1)
