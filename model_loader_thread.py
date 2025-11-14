from faster_whisper import WhisperModel
from PyQt6.QtCore import QThread, pyqtSignal


class ModelLoaderThread(QThread):
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, model_path, device="cpu", compute_type="float32", cpu_threads=3):
        super().__init__()
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self.cpu_threads = cpu_threads

    def run(self):
        try:
            model = WhisperModel(
                model_size_or_path=self.model_path,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads,
                local_files_only=True
            )
            self.finished_signal.emit(model)
        except Exception as e:
            self.error_signal.emit(str(e))