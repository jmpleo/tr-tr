import os
import logging
from transformers import MarianMTModel, MarianTokenizer


class OpusMt:
    def __init__(self, model_path):
        self.tokenizer = MarianTokenizer.from_pretrained(model_path)
        self.model = MarianMTModel.from_pretrained(model_path)

    def translate(self, texts):

        translated = self.model.generate(
            **self.tokenizer(texts, return_tensors="pt", padding=True)
        )

        return [
            self.tokenizer.decode(t, skip_special_tokens=True)
            for t in translated
        ]


class Translation:
    def __init__(self, translate_model_paths):
        self.translate_model_paths = translate_model_paths
        self.translation_models = {}

    def clear_cache(self):
        self.translation_models.clear()

    def load_translation_model(self, from_lang, target_lang):
        key = (from_lang, target_lang)
        if key in self.translation_models:
            return self.translation_models[key]

        if key in self.translate_model_paths:
            model_path = self.translate_model_paths[key]
            if not os.path.exists(model_path):
                logging.warning(f"Model path does not exist: {model_path}")
                return None

            self.translation_models[key] = OpusMt(model_path)

            logging.info(f"Translation model for {from_lang}-{target_lang} loaded successfully")
            return self.translation_models[key]
        else:
            logging.warning(f"No translation model available for language: {from_lang}-{target_lang}")
            return None
