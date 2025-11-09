import gradio as gr
from faster_whisper import WhisperModel
from transformers import pipeline
import os
import logging
import traceback
from datetime import datetime


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


styles = ""
with open('style.css') as s:
    styles = s.read()

save_dir = os.path.join(os.path.expanduser("~"), 'tr-tr')
if not os.path.exists(save_dir):
    os.makedirs(save_dir, exist_ok=True)

try:
    transcribe_model = WhisperModel('./repo/Systran/faster-whisper-small')
    logger.info("Transcription model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load transcription model: {e}")
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
                logger.warning(f"Model path does not exist: {model_path}")
                return None

            model = pipeline("translation", model=model_path)

            translation_models[from_lang, target_lang] = model
            logger.info(f"Translation model for {from_lang}-{target_lang} loaded successfully")
            return model
        else:
            logger.warning(f"No translation model available for language: {from_lang}-{target_lang}")
            return None
    except Exception as e:
        logger.error(f"Failed to load translation model for {from_lang}-{target_lang}: {e}")
        return None


def save_to_txt(save_dir, segments, prefix=""):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = os.path.join(save_dir, f"{prefix}_{timestamp}.txt")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            if not segments:
                f.write("Речь в аудио не распознана\n")
                return filename

            for start, end, text, translations in segments:
                try:
                    f.write(f"[{start:.2f}s - {end:.2f}s]\n")
                    f.write(f"Речь: {text}\n")
                    for target_lang, text_t in translations.items():
                        f.write(f"Перевод ({target_lang}): {text_t}\n")
                    f.write("-" * 40 + "\n")
                except Exception as e:
                    logger.error(f"Error saving segment to TXT: {e}")
                    f.write("Ошибка форматирования сегмента\n")
                    f.write("-" * 40 + "\n")

        logger.info(f"Results saved to: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        return None

def transcribe_translate(audio_file, target_langs, progress=gr.Progress()):
    if transcribe_model is None:
        yield 0, 0, "Ошибка: выбранная модель не загрузилась", {}
        return

    if not audio_file or not os.path.exists(audio_file):
        yield 0, 0, f"Ошибка: {audio_file} недоступен", {}
        return

    try:
        segments, info = transcribe_model.transcribe(audio_file)

        detected_language = info.language if hasattr(info, 'language') else None

        progress(0.15, desc=f"Распознавание с '{detected_language}'...")
        logger.info(f"Detected language: {detected_language}")

        translate_models = {}
        if target_langs is not None:
            for target_lang in target_langs:
                if (detected_language, target_lang) in translate_model_paths:
                    translate_models[target_lang] = load_translation_model(detected_language, target_lang)
                    progress(0.25, desc=f"Инициализация переводчика {detected_language}-{target_lang}...")

        for i, segment in enumerate(segments, 1):
            progress(0.5, desc=f"Распознавание {i} сегмента...")

            text = segment.text.strip() if segment.text else ""
            text_t = {}
            for target_lang, translate_model in translate_models.items():
                try:
                    text_t[target_lang] = translate_model(text)[0]['translation_text']
                    progress(0.5, desc=f"Перевод {i} сегмента ({detected_language}-{target_lang})...")
                except Exception as e:
                    logger.error(f"Translation failed: {e}")
                    text_t[target_lang] = "Ошибка перевода"

            yield segment.start, segment.end, text, text_t

    except Exception as e:
        logger.error(f"Transcription/translation failed: {e}")
        yield 0, 0, "", {}


def format_output(segments):
    if not segments:
        return "<div class='result-container'><p class='no-speech'>Речь в аудио не распознана</p></div>"

    html_output = "<div class='result-container'>"

    for start, end, text, translations in segments:
        try:
            html_output += f"""<div class='segment translation-segment'>
                <small class='timestamp'>[{start:.2f}s - {end:.2f}s]</small>
                <p class='text'>{text}</p>"""
            for target_lang, text_t in translations.items():
                html_output += f"<p class='translation'><strong>({target_lang})</strong> {text_t}</p>"
            html_output +="</div>"
        except Exception as e:
            logger.error(f"Error formatting segment: {e}")
            html_output += f"""
            <div class='segment error-segment'>
                <p class='error-text'>Ошибка форматирования результата</p>
            </div>
            """

    html_output += "</div>"
    return html_output


def result_error(text):
    return f"<div class='result-container'><p class='error'>{text}</p></div>"


def process(audio_file, target_langs, progress=gr.Progress()):
    if not audio_file:
        return result_error('Загрузите аудио')

    if transcribe_model is None:
        return result_error('Модель транскрипции недоступна')

    try:
        progress(0, desc="Инициализация...")

        segments = list(transcribe_translate(audio_file, target_langs, progress))

        progress(0.95, desc=f"Сохранение в файл...")

        txt_filename = save_to_txt(
            save_dir=save_dir,
            segments=segments,
            prefix=os.path.basename(audio_file).replace('.', '_')
        )

        progress(1.0, desc="Завершено")

        html_result = format_output(segments)

        if txt_filename:
            html_result += f"""
            <div class='save-info'>
                <p>Результаты сохранены в файл: <strong>{txt_filename}</strong></p>
            </div>
            """
        else:
            html_result += """
            <div class='save-info error'>
                <p>Не удалось сохранить результаты в файл</p>
            </div>
            """

        return html_result

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        logger.error(traceback.format_exc())
        return result_error(f'Во время обработки произошла ошибка: {str(e)}')


interface = gr.Interface(
    title="Распознование речи без этих ваших интернетов",
    description="",
    flagging_mode="never",
    css=styles,
    inputs=[
        gr.Audio(
            type="filepath",
            label="Загрузить аудио",
            sources=["upload", "microphone"],
        ),
        gr.CheckboxGroup(
            choices=[
                ("Английский", "en"),
                ("Русский", "ru")
            ],
            label="Перевод",
            info=f"""Дополнительно переводить для поддерживаемых языков ({', '.join(
                f'{from_lang}-{target_lang}'
                for from_lang, target_lang in translate_model_paths
            )})""",
        ),
        # gr.Checkbox(
        #     label="Перевод на русский",
        #     value=False,
        #     info=f"Дополнительно переводить с поддерживаемых языков ({','.join(translate_model_paths.keys())})",
        # ),
        # gr.FileExplorer(
        #     label="Директория для результата",
        #     file_count="single",
        #     root_dir=os.path.expanduser("~"),
        #     glob="**/*",
        #     ignore_glob=".*/",
        #     max_height=300
        # )
    ],
    submit_btn="Распознать речь",
    stop_btn="Остановить",
    clear_btn="Убрать",
    fn=process,
    outputs=gr.HTML()
)


if __name__ == "__main__":
    try:
        interface.launch(
            server_name="127.0.0.1",
            share=False,
            show_error=False,
            max_threads=1,
            show_api=False,
            inbrowser=True
        )
    except Exception as e:
        logger.error(f"Failed to launch interface: {e}")
        print(f"Error: {e}")
