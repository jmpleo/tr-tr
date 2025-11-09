import os
import logging
from transformers import pipeline


class Translation:
    def __init__(self, translate_model_paths):
        self.translate_model_paths = translate_model_paths
        self.translation_models = {}

    def load_translation_model(self, from_lang, target_lang):
        if (from_lang, target_lang) in self.translation_models:
            return self.translation_models[from_lang, target_lang]
        try:
            if (from_lang, target_lang) in self.translate_model_paths:
                model_path = self.translate_model_paths[from_lang, target_lang]
                if not os.path.exists(model_path):
                    logging.warning(f"Model path does not exist: {model_path}")
                    return None

                model = pipeline("translation", model=model_path)
                self.translation_models[from_lang, target_lang] = model
                logging.info(f"Translation model for {from_lang}-{target_lang} loaded successfully")
                return model
            else:
                logging.warning(f"No translation model available for language: {from_lang}-{target_lang}")
                return None
        except Exception as e:
            logging.error(f"Failed to load translation model for {from_lang}-{target_lang}: {e}")
            return None