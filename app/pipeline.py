import os

from app.pib_scraper import fetch_press_release
from app.summarizer import summarize_release
from app.Translator import translate_bullets
from app.tts import generate_speech
from app.video_generator import create_video


OUTPUT_ROOT = "output/videos"


def bullets_to_narration(bullets):
    return ". ".join(
        line.strip().rstrip(".")
        for line in bullets
    ) + "."


def save_text(filename, text):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)


def generate_video_for_release(prid, language):

    print("=" * 70)
    print("PIB VIDEO GENERATION PIPELINE")
    print("=" * 70)

    print(f"\nPRID     : {prid}")
    print(f"Language : {language}")

    # ---------------------------------------------------------
    # 1. FETCH RELEASE
    # ---------------------------------------------------------
    print("\n[1/5] Fetching PIB press release...")

    try:
        release = fetch_press_release(prid)

    except Exception as e:
        return {
            "status": "FAILED",
            "stage": "fetch",
            "error": str(e),
            "prid": prid,
            "language": language,
            "video_file": None,
        }

    print("Title      :", release.title)
    print("Word count :", release.word_count)

    # ---------------------------------------------------------
    # CREATE OUTPUT FOLDERS
    # ---------------------------------------------------------
    release_folder = os.path.join(
        OUTPUT_ROOT,
        f"release_{release.prid}"
    )

    translations_folder = os.path.join(
        release_folder,
        "translations"
    )

    audio_folder = os.path.join(
        release_folder,
        "audio"
    )

    videos_folder = os.path.join(
        release_folder,
        "videos"
    )

    os.makedirs(translations_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)
    os.makedirs(videos_folder, exist_ok=True)

    # Save original release
    original_file = os.path.join(
        release_folder,
        "original.txt"
    )

    save_text(
        original_file,
        release.title + "\n\n" + release.body
    )

    # ---------------------------------------------------------
    # 2. SUMMARIZATION
    # ---------------------------------------------------------
    print("\n[2/5] Generating English summary...")

    try:
        summary = summarize_release(
            title=release.title,
            body=release.body,
            max_bullets=4
        )

    except Exception as e:
        return {
            "status": "FAILED",
            "stage": "summarization",
            "error": str(e),
            "prid": release.prid,
            "title": release.title,
            "language": language,
            "original_file": original_file,
            "video_file": None,
        }

    english_bullets = summary.bullet_points

    print("\nEnglish summary:")

    for i, bullet in enumerate(
        english_bullets,
        start=1
    ):
        print(f"{i}. {bullet}")

    # ---------------------------------------------------------
    # 3. TRANSLATION
    # ---------------------------------------------------------
    print(f"\n[3/5] Preparing {language} text...")

    try:

        if language == "English":

            translated_bullets = english_bullets

        else:

            translation_result = translate_bullets(
                english_bullets,
                language
            )

            translated_bullets = (
                translation_result.translated_bullets
            )

    except Exception as e:

        return {
            "status": "FAILED",
            "stage": "translation",
            "error": str(e),
            "prid": release.prid,
            "title": release.title,
            "language": language,
            "original_file": original_file,
            "video_file": None,
        }

    narration_text = bullets_to_narration(
        translated_bullets
    )

    translation_file = os.path.join(
        translations_folder,
        f"{language.lower()}.txt"
    )

    save_text(
        translation_file,
        narration_text
    )

    print(
        "Translation saved:",
        translation_file
    )

    # ---------------------------------------------------------
    # 4. TEXT TO SPEECH
    # ---------------------------------------------------------
    print(f"\n[4/5] Generating {language} audio...")

    audio_file = os.path.join(
        audio_folder,
        f"{language.lower()}.mp3"
    )

    try:

        speech_result = generate_speech(
            narration_text,
            language,
            audio_file
        )
            
        audio_file = speech_result.filename

        print(
            "Audio generated:",
            speech_result.filename
        )


    except Exception as e:

        return {
            "status": "FAILED",
            "stage": "tts",
            "error": str(e),
            "prid": release.prid,
            "title": release.title,
            "language": language,
            "original_file": original_file,
            "translation_file": translation_file,
            "audio_file": None,
            "video_file": None,
        }

    # ---------------------------------------------------------
    # 5. VIDEO GENERATION
    # ---------------------------------------------------------
    print(f"\n[5/5] Generating {language} video...")

    video_file = os.path.join(
        videos_folder,
        f"{language.lower()}.mp4"
    )

    try:

        create_video(
            title=release.title,
            summary_text=narration_text,
            audio_file=audio_file,
            output_video=video_file,
            language=language
        )

    except Exception as e:

        return {
            "status": "FAILED",
            "stage": "video",
            "error": str(e),
            "prid": release.prid,
            "title": release.title,
            "language": language,
            "original_file": original_file,
            "translation_file": translation_file,
            "audio_file": audio_file,
            "video_file": None,
        }

    print("\nVIDEO GENERATED SUCCESSFULLY")
    print(video_file)

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED")
    print("=" * 70)

    # ---------------------------------------------------------
    # UI-FRIENDLY SUCCESS RESULT
    # ---------------------------------------------------------
    return {
        "status": "SUCCESS",
        "prid": release.prid,
        "title": release.title,
        "language": language,

        "original_file": original_file,
        "translation_file": translation_file,
        "audio_file": audio_file,
        "video_file": video_file,

        "summary": english_bullets,
        "narration": narration_text,
    }