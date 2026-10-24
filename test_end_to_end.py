import os

from app.pib_scraper import list_releases, fetch_press_release
from app.summarizer import summarize_release
from app.Translator import translate_bullets
from app.tts import generate_speech
from app.video_generator import create_video


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_ROOT = "output/end_to_end"

LANGUAGES = [
    "English",
    "Hindi",
    "Urdu",
    "Punjabi",
    "Gujarati",
    "Marathi",
    "Telugu",
    "Kannada",
    "Malayalam",
    "Tamil",
    "Bengali",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def make_directories(release_folder):
    """Create folders required for the pipeline."""

    folders = [
        release_folder,
        os.path.join(release_folder, "translations"),
        os.path.join(release_folder, "audio"),
        os.path.join(release_folder, "videos"),
    ]

    for folder in folders:
        os.makedirs(folder, exist_ok=True)


def save_text(filename, text):
    """Save text using UTF-8 encoding."""

    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)


def bullets_to_narration(bullets):
    """
    Convert bullet points into one narration string.
    """

    return ". ".join(
        line.strip().rstrip(".")
        for line in bullets
    ) + "."


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("=" * 70)
    print("        PIB PRESS RELEASE → MULTILINGUAL VIDEO PIPELINE")
    print("=" * 70)


    # ========================================================
    # STEP 1: FIND LATEST PIB RELEASE
    # ========================================================

    print("\n[1/6] Finding latest PIB press release...")
    print("-" * 70)

    releases = list_releases()

    if not releases:
        print("ERROR: No PIB releases found.")
        return

    latest_release = releases[0]

    print("Latest release found:")
    print("PRID :", latest_release.prid)
    print("Title:", latest_release.title)


    # ========================================================
    # STEP 2: FETCH COMPLETE PRESS RELEASE
    # ========================================================

    print("\n[2/6] Fetching complete press release...")
    print("-" * 70)

    release = fetch_press_release(latest_release.prid)

    print("Title      :", release.title)
    print("Word count :", release.word_count)

    release_folder = os.path.join(
        OUTPUT_ROOT,
        f"release_{release.prid}"
    )

    make_directories(release_folder)

    # Save original release
    original_file = os.path.join(
        release_folder,
        "original.txt"
    )

    save_text(
        original_file,
        release.title + "\n\n" + release.body
    )

    print("Original release saved:")
    print(original_file)


    # ========================================================
    # STEP 3: SUMMARIZE
    # ========================================================

    print("\n[3/6] Summarizing press release...")
    print("-" * 70)

    summary = summarize_release(
        title=release.title,
        body=release.body,
        max_bullets=4
    )

    # IMPORTANT:
    # Your Summary dataclass uses "bullet_points"
    english_bullets = summary.bullet_points

    print("\nGenerated English summary:")

    for i, bullet in enumerate(
        english_bullets,
        start=1
    ):
        print(f"{i}. {bullet}")

    english_narration = bullets_to_narration(
        english_bullets
    )

    # Save English summary
    summary_file = os.path.join(
        release_folder,
        "summary.txt"
    )

    save_text(
        summary_file,
        english_narration
    )

    print("\nSummary saved:")
    print(summary_file)


    # ========================================================
    # STEP 4: TRANSLATION + TTS + VIDEO
    # ========================================================

    print("\n[4/6] Processing all languages...")
    print("-" * 70)

    results = {}


    # ========================================================
    # PROCESS EACH LANGUAGE
    # ========================================================

    for language in LANGUAGES:

        print("\n")
        print("=" * 70)
        print(f"PROCESSING: {language}")
        print("=" * 70)

        try:

            # ------------------------------------------------
            # ENGLISH
            # ------------------------------------------------

            if language == "English":

                translated_bullets = english_bullets

            # ------------------------------------------------
            # OTHER LANGUAGES
            # ------------------------------------------------

            else:

                print(
                    f"\nTranslating English → {language}..."
                )

                translation_result = translate_bullets(
                    english_bullets,
                    language
                )

                translated_bullets = (
                    translation_result.translated_bullets
                )

            # ------------------------------------------------
            # DISPLAY TRANSLATION
            # ------------------------------------------------

            print("\nTranslated text:")

            for i, line in enumerate(
                translated_bullets,
                start=1
            ):
                print(f"{i}. {line}")

            # ------------------------------------------------
            # CREATE NARRATION
            # ------------------------------------------------

            narration_text = bullets_to_narration(
                translated_bullets
            )

            # ------------------------------------------------
            # SAVE TRANSLATION
            # ------------------------------------------------

            translation_file = os.path.join(
                release_folder,
                "translations",
                f"{language.lower()}.txt"
            )

            save_text(
                translation_file,
                narration_text
            )

            print("\nTranslation saved:")
            print(translation_file)

            # ------------------------------------------------
            # GENERATE AUDIO
            # ------------------------------------------------

            audio_file = os.path.join(
                release_folder,
                "audio",
                f"{language.lower()}.mp3"
            )

            print(
                f"\nGenerating {language} audio..."
            )

            speech_result = generate_speech(
                narration_text,
                language,
                audio_file
            )

            print("Audio generated:")
            print(speech_result.filename)

            # ------------------------------------------------
            # GENERATE VIDEO
            # ------------------------------------------------

            video_file = os.path.join(
                release_folder,
                "videos",
                f"{language.lower()}.mp4"
            )

            print(
                f"\nGenerating {language} video..."
            )

            create_video(
                title=release.title,
                summary_text=narration_text,
                audio_file=audio_file,
                output_video=video_file,
                language=language
            )

            print(
                "\nVIDEO GENERATED SUCCESSFULLY:"
            )
            print(video_file)

            results[language] = "SUCCESS"

        except Exception as e:

            results[language] = f"FAILED: {e}"

            print(
                f"\nERROR while processing {language}:"
            )
            print(e)


    # ========================================================
    # STEP 5: SAVE RESULTS
    # ========================================================

    print("\n[5/6] Saving pipeline results...")
    print("-" * 70)

    results_file = os.path.join(
        release_folder,
        "pipeline_results.txt"
    )

    with open(
        results_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "PIB PRESS RELEASE TO VIDEO PIPELINE\n"
        )

        file.write("=" * 60 + "\n\n")

        file.write(
            f"PRID: {release.prid}\n"
        )

        file.write(
            f"Title: {release.title}\n"
        )

        file.write(
            f"Word Count: {release.word_count}\n\n"
        )

        file.write("RESULTS\n")
        file.write("-" * 60 + "\n")

        for language, result in results.items():

            file.write(
                f"{language}: {result}\n"
            )

    print("Results saved:")
    print(results_file)


    # ========================================================
    # STEP 6: FINAL REPORT
    # ========================================================

    print("\n[6/6] PIPELINE COMPLETED")
    print("=" * 70)

    print("\nFINAL RESULTS")
    print("=" * 70)

    for language, result in results.items():

        print(
            f"{language:<12}: {result}"
        )

    print("\nAll generated files are inside:")
    print(release_folder)

    print("\nVideos are inside:")
    print(
        os.path.join(
            release_folder,
            "videos"
        )
    )

    print("\n" + "=" * 70)


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":
    main()