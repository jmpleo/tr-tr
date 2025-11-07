import gradio as gr
from faster_whisper import WhisperModel
from transformers import pipeline
import os
import logging
import traceback

from style import style_css


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


try:
    transcribe_model = WhisperModel('./repo/Systran/faster-whisper-small')
    logger.info("Transcription model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load transcription model: {e}")
    transcribe_model = None

translate_model_paths = {
    'he': './repo/Helsinki-NLP/opus-mt-tc-big-he-en',
    'ar': './repo/Helsinki-NLP/opus-mt-tc-big-ar-en',
}

translation_models = {}

def load_translation_model(language):
    if language in translation_models:
        return translation_models[language]
    try:
        if language in translate_model_paths:
            model_path = translate_model_paths[language]
            if not os.path.exists(model_path):
                logger.warning(f"Model path does not exist: {model_path}")
                return None

            model = pipeline("translation", model=model_path)

            translation_models[language] = model
            logger.info(f"Translation model for {language} loaded successfully")
            return model
        else:
            logger.warning(f"No translation model available for language: {language}")
            return None
    except Exception as e:
        logger.error(f"Failed to load translation model for {language}: {e}")
        return None


def transcribe(audio_file, progress=gr.Progress()):
    if transcribe_model is None:
        yield 0, 0, "Ошибка: модель недоступна"
        return

    if not audio_file or not os.path.exists(audio_file):
        yield 0, 0, f"Ошибка: не существует аудио {audio_file}"
        return

    try:
        segments, _ = transcribe_model.transcribe(audio_file)
        segments_list = list(segments)
        total_segments = len(segments_list)

        for i, segment in enumerate(segments_list):
            try:
                text = segment.text.strip() if segment.text else ""
                progress((i, total_segments), desc="Транскрибирование...")
                yield segment.start, segment.end, text
            except Exception as e:
                logger.error(f"Error processing segment: {e}")
                yield segment.start, segment.end, f"Ошибка: {str(e)}"

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        yield 0, 0, f"Ошибка: {str(e)}"


def transcribe_translate(audio_file, progress=gr.Progress()):
    if transcribe_model is None:
        yield 0, 0, "Ошибка: модель недоступна", ""
        return

    if not audio_file or not os.path.exists(audio_file):
        yield 0, 0, f"Ошибка: не существует аудио {audio_file}", ""
        return

    try:
        segments, info = transcribe_model.transcribe(audio_file)
        segments_list = list(segments)
        total_segments = len(segments_list)

        detected_language = info.language if hasattr(info, 'language') else None

        logger.info(f"Detected language: {detected_language}")

        translate_model = None
        if detected_language in translate_model_paths:
            translate_model = load_translation_model(detected_language)

        for i, segment in enumerate(segments_list):
            try:
                text = segment.text.strip() if segment.text else ""

                if translate_model:
                    try:
                        progress((i, total_segments), desc="Перевод...")
                        text_en = translate_model(text)[0]['translation_text']
                    except Exception as e:
                        logger.error(f"Translation failed: {e}")
                        text_en = f"Ошибка перевода: {str(e)}"
                else:
                    text_en = "Нет доступной модели для перевода этого языка"

                yield segment.start, segment.end, text, text_en

            except Exception as e:
                logger.error(f"Error processing segment: {e}")
                yield segment.start, segment.end, f"Ошибка: {str(e)}", "Проблема при переводе"

    except Exception as e:
        logger.error(f"Transcription/translation failed: {e}")
        yield 0, 0, f"Проблема при транскрибации: {str(e)}", ""


def format_output(segments, include_translation=False):
    if not segments:
        return "<div class='result-container'><p class='no-speech'>Речь в аудио не распознана</p></div>"

    html_output = "<div class='result-container'>"

    for segment in segments:
        try:
            if include_translation and len(segment) == 4:
                start, end, text, translation = segment
                html_output += f"""
                <div class='segment translation-segment'>
                    <small class='timestamp'>[{start:.2f}s - {end:.2f}s]</small>
                    <p class='text'><strong>Речь:</strong> {text}</p>
                    <p class='translation'><strong>Перевод:</strong> {translation}</p>
                </div>
                """
            elif len(segment) == 3:
                start, end, text = segment
                html_output += f"""
                <div class='segment transcription-segment'>
                    <small class='timestamp'>[{start:.2f}s - {end:.2f}s]</small>
                    <p class='text'>{text}</p>
                </div>
                """
        except Exception as e:
            logger.error(f"Error formatting segment: {e}")
            html_output += f"""
            <div class='segment error-segment'>
                <p class='error-text'>Ошибка форматирования результата</p>
            </div>
            """

    html_output += "</div>"
    return html_output

def process(audio_file, text_en_checkbox, progress=gr.Progress()):
    if not audio_file:
        return "<div class='result-container'><p class='error'>Загрузите аудио</p></div>"

    if transcribe_model is None:
        return "<div class='result-container'><p class='error'>Модель транскрипции недоступна.</p></div>"

    try:
        progress(0, desc="Начало обработки...")

        if text_en_checkbox:
            segments = list(transcribe_translate(audio_file, progress))
        else:
            segments = list(transcribe(audio_file, progress))

        progress(1.0, desc="Обработка завершена!")
        return format_output(segments, text_en_checkbox)

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        logger.error(traceback.format_exc())
        return f"<div class='result-container'><p class='error'>Во время обработки произошла ошибка: {str(e)}</p></div>"


interface = gr.Interface(
    title="Распознавание речи",
    description="Поддерживаются множество языков для распознования. Перевод доступен только для Иврита и Арабского.",
    allow_flagging="never",
    css=style_css,
    inputs=[
        gr.Audio(
            type="filepath",
            label="Загрузить аудио",
            sources=["upload", "microphone"],
        ),
        gr.Checkbox(
            label="Перевод на английский",
            value=True,
            info="Включить перевод для поддерживаемых языков",
        )
    ],
    submit_btn="Распознать речь",
    stop_btn="Остановить",
    clear_btn="Убрать",
    fn=process,
    outputs=gr.HTML(
        label="Результат",
        show_label=True
    )
)


if __name__ == "__main__":
    try:
        interface.launch(
            server_name="127.0.0.1",
            share=False,
            show_error=True
        )
    except Exception as e:
        logger.error(f"Failed to launch interface: {e}")
        print(f"Error: {e}")