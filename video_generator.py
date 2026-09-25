from moviepy import AudioFileClip, ImageSequenceClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import unicodedata


WIDTH = 1280
HEIGHT = 720
FPS = 12


# ============================================================
# FONT FUNCTIONS
# ============================================================

# Language-specific fonts available in the Ubuntu/WSL environment.
# The same language font is used for the title and main content.
# English UI elements continue to use DejaVu Sans.
LANGUAGE_FONT_PATHS = {
    "English": {
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    },
    "Hindi": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    },
    "Urdu": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
    },
    "Punjabi": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansGurmukhi-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansGurmukhi-Bold.ttf",
    },
    "Gujarati": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansGujarati-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansGujarati-Bold.ttf",
    },
    "Marathi": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    },
    "Telugu": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansTelugu-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansTelugu-Bold.ttf",
    },
    "Kannada": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansKannada-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansKannada-Bold.ttf",
    },
    "Malayalam": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansMalayalam-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansMalayalam-Bold.ttf",
    },
    "Tamil": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf",
    },
    "Bengali": {
        "regular": "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
        "bold": "/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf",
    }
}


def get_language_font(language, size, bold=False):
    """
    Loads the correct font for the selected language.

    This replaces the old Telugu-only font selection.
    """

    if language not in LANGUAGE_FONT_PATHS:
        language = "English"

    font_type = "bold" if bold else "regular"
    font_path = LANGUAGE_FONT_PATHS[language][font_type]

    try:
        return ImageFont.truetype(
            font_path,
            size
        )

    except:
        return ImageFont.load_default()


def get_english_font(size, bold=False):
    """
    Loads an English-supported font.
    """

    if bold:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    else:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    try:
        return ImageFont.truetype(
            font_path,
            size
        )

    except:
        return ImageFont.load_default()


def get_mixed_font(size, bold=False):
    """
    Kept for compatibility with older code.
    The current video generator selects fonts by language.
    """

    return get_language_font(
        "English",
        size,
        bold
    )


# ============================================================
# BACKGROUND
# ============================================================

def create_background(progress):
    """
    Creates a static blue news-style background.

    The background does not move.
    """

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT)
    )

    pixels = image.load()

    for y in range(HEIGHT):

        for x in range(WIDTH):

            # Static gradient
            r = 10 + int(
                (x / WIDTH) * 20
            )

            g = 25 + int(
                (y / HEIGHT) * 35
            )

            b = 70 + int(
                (x / WIDTH) * 70
            )

            pixels[x, y] = (
                r,
                g,
                b
            )

    return image


# ============================================================
# HEADER
# ============================================================

def draw_header(draw, scene_number):

    # English font for English header
    font = get_english_font(
        28,
        bold=True
    )

    draw.rectangle(
        (0, 0, WIDTH, 80),
        fill=(0, 0, 0)
    )

    draw.text(
        (40, 22),
        "PRESS INFORMATION BUREAU",
        fill="white",
        font=font
    )

    scene_text = (
        f"SCENE {scene_number}"
    )

    draw.text(
        (WIDTH - 180, 22),
        scene_text,
        fill=(200, 200, 200),
        font=font
    )


# ============================================================
# WRAPPED TEXT
# ============================================================

def draw_wrapped_text(
    draw,
    text,
    font,
    x,
    y,
    max_width,
    line_spacing=15,
    fill="white"
):

    words = text.split()

    lines = []

    current_line = ""

    for word in words:

        if current_line:

            test_line = (
                current_line
                + " "
                + word
            )

        else:

            test_line = word

        if draw.textlength(
            test_line,
            font=font
        ) <= max_width:

            current_line = test_line

        else:

            if current_line:

                lines.append(
                    current_line
                )

            current_line = word

    if current_line:

        lines.append(
            current_line
        )

    for line in lines:

        draw.text(
            (x, y),
            line,
            font=font,
            fill=fill
        )

        y += (
            font.size
            + line_spacing
        )

    return y


# ============================================================
# LANGUAGE-SPECIFIC CONTENT FONT
# ============================================================

def get_content_font(
    language,
    size,
    bold=False
):
    """
    Selects the correct font for the title/main content based
    on the selected video language.
    """

    return get_language_font(
        language,
        size,
        bold
    )


# ============================================================
# TELUGU-SAFE CHARACTER SPLITTING
# ============================================================

def split_into_display_units(text):
    """
    Splits text into visual letter-like units.

    Combining marks are kept attached to the previous
    Telugu character so Telugu characters do not break.
    """

    units = []

    current = ""

    for char in text:

        # Combining marks
        if (
            unicodedata.category(char).startswith("M")
            or char in (
                "\u200c",
                "\u200d"
            )
        ):

            current += char

        else:

            if current:

                units.append(
                    current
                )

            current = char

    if current:

        units.append(
            current
        )

    return units


# ============================================================
# SCENE FRAME GENERATION
# ============================================================

def create_scene_frames(
    scene_number,
    title,
    text,
    duration,
    language
):
    """
    Creates animated frames for one scene.

    Text is revealed letter-by-letter while maintaining
    the narration-based timing.
    """

    total_frames = max(
        1,
        int(duration * FPS)
    )

    frames = []

    # ------------------------------------------------
    # Release title is always in English,
    # so always use the English font for the moving title.
    # ------------------------------------------------

    title_font = get_content_font(
        "English",
        34,
        bold=True
    )

    title_bbox = title_font.getbbox(title)

    title_width = (
        title_bbox[2]
        - title_bbox[0]
    )
    # ------------------------------------------------
    # Select content font
    # ------------------------------------------------

    text_font = get_content_font(
        language,
        34
    )

    # English footer
    small_font = get_english_font(
        24
    )

    # ------------------------------------------------
    # Split content into display units
    # ------------------------------------------------

    display_units = (
        split_into_display_units(
            text
        )
    )

    total_units = len(
        display_units
    )

    # ========================================================
    # FRAME LOOP
    # ========================================================

    for frame_number in range(
        total_frames
    ):

        # Progress through scene
        progress = (
            frame_number
            / max(
                total_frames - 1,
                1
            )
        )

        # ------------------------------------------------
        # Background
        # ------------------------------------------------

        image = create_background(
            progress
        )

        draw = ImageDraw.Draw(
            image
        )

        # ------------------------------------------------
        # Header
        # ------------------------------------------------

        draw_header(
            draw,
            scene_number
        )


        # ------------------------------------------------
        # Animated scrolling title
        # ------------------------------------------------

        start_x = WIDTH

        end_x = -title_width

        title_x = int(
            start_x
            + (end_x - start_x) * progress
        )

        draw.text(
            (title_x, 150),
            title,
            font=title_font,
            fill="white"
        )

        # ------------------------------------------------
        # Main information box
        # ------------------------------------------------

        box_top = 250

        draw.rounded_rectangle(
            (
                50,
                box_top,
                WIDTH - 50,
                610
            ),
            radius=25,
            fill=(0, 0, 0, 180)
        )

        # ========================================================
        # LETTER-BY-LETTER REVEAL
        # ========================================================

        reveal_progress = min(
            progress / 0.80,
            1
        )

        if total_units > 0:

            visible_units = int(
                total_units
                * reveal_progress
            )

            visible_units = max(
                1,
                min(
                    visible_units,
                    total_units
                )
            )

            visible_text = "".join(
                display_units[
                    :visible_units
                ]
            )

        else:

            visible_text = text

        # ------------------------------------------------
        # Draw text
        # ------------------------------------------------

        draw_wrapped_text(
            draw,
            visible_text,
            text_font,
            90,
            310,
            WIDTH - 180,
            line_spacing=18
        )

        # ------------------------------------------------
        # Bottom progress bar
        # ------------------------------------------------

        progress_width = int(
            (WIDTH - 100)
            * progress
        )

        draw.rectangle(
            (
                50,
                650,
                50 + progress_width,
                660
            ),
            fill=(255, 255, 255)
        )

        # ------------------------------------------------
        # Footer
        # ------------------------------------------------

        draw.text(
            (50, 680),
            "AI GENERATED NEWS VIDEO",
            font=small_font,
            fill=(220, 220, 220)
        )

        # ------------------------------------------------
        # Save frame
        # ------------------------------------------------

        frames.append(
            np.array(image)
        )

    return frames


# ============================================================
# SCENE TIMING
# ============================================================

def calculate_scene_durations(
    scene_texts,
    total_duration
):
    """
    Calculates approximate narration duration for each scene
    based on word count.

    Longer sentences receive more screen time.
    """

    word_counts = []

    for text in scene_texts:

        count = len(
            text.split()
        )

        word_counts.append(
            max(
                count,
                1
            )
        )

    total_words = sum(
        word_counts
    )

    scene_durations = []

    for count in word_counts:

        duration = (
            total_duration
            * count
            / total_words
        )

        scene_durations.append(
            duration
        )

    return scene_durations


# ============================================================
# CREATE VIDEO
# ============================================================

def create_video(
    title,
    summary_text,
    audio_file,
    output_video,
    language="English"
):

    print(
        "Creating AI news video..."
    )
    print(
        f"Video language: {language}"
    )

    os.makedirs(
        os.path.dirname(
            output_video
        ),
        exist_ok=True
    )

    # ========================================================
    # LOAD AUDIO
    # ========================================================

    audio = AudioFileClip(
        audio_file
    )

    total_duration = audio.duration

    print(
        f"Narration duration: "
        f"{total_duration:.2f} seconds"
    )

    # ========================================================
    # PREPARE SUMMARY
    # ========================================================

    summary_text = (
        summary_text.strip()
    )

    # ========================================================
    # SPLIT SUMMARY INTO SENTENCES
    # ========================================================

    sentences = [
        sentence.strip()
        for sentence in
        summary_text
        .replace("!", ".")
        .replace("?", ".")
        .split(".")
        if sentence.strip()
    ]

    if len(sentences) == 0:

        sentences = [
            summary_text
        ]

    # ========================================================
    # CREATE SCENES
    # ========================================================

    scene_count = min(
        len(sentences),
        4
    )

    # --------------------------------------------------------
    # If more than 4 sentences, combine them
    # --------------------------------------------------------

    if len(sentences) > 4:

        sentences_per_scene = (
            len(sentences) // 4
        )

        scene_texts = []

        for i in range(4):

            start = (
                i
                * sentences_per_scene
            )

            if i == 3:

                end = len(
                    sentences
                )

            else:

                end = (
                    start
                    + sentences_per_scene
                )

            scene_text = " ".join(
                sentences[
                    start:end
                ]
            )

            scene_texts.append(
                scene_text
            )

    else:

        scene_texts = sentences

    scene_count = len(
        scene_texts
    )

    # ========================================================
    # CALCULATE SCENE TIMING
    # ========================================================

    scene_durations = (
        calculate_scene_durations(
            scene_texts,
            total_duration
        )
    )

    print()
    print(
        "Scene timing:"
    )

    for i, duration in enumerate(
        scene_durations
    ):

        print(
            f"Scene {i + 1}: "
            f"{duration:.2f} seconds | "
            f"{len(scene_texts[i].split())} words"
        )

    print()

    # ========================================================
    # GENERATE SCENES
    # ========================================================

    all_frames = []

    for index, scene_text in enumerate(
        scene_texts
    ):

        scene_number = (
            index + 1
        )

        # ------------------------------------------------
        # First scene uses actual release title
        # ------------------------------------------------

        if scene_number == 1:

            scene_title = title

        else:

            scene_title = (
                f"KEY INFORMATION "
                f"{scene_number}"
            )

        print(
            f"Generating Scene "
            f"{scene_number}..."
        )

        print(
            f"Scene text: "
            f"{scene_text}"
        )

        print(
            f"Scene duration: "
            f"{scene_durations[index]:.2f} seconds"
        )

        # ------------------------------------------------
        # Generate frames
        # ------------------------------------------------

        frames = create_scene_frames(
            scene_number,
            scene_title,
            scene_text,
            scene_durations[index],
            language
        )

        all_frames.extend(
            frames
        )

    # ========================================================
    # CREATE VIDEO
    # ========================================================

    print()
    print(
        "Creating video sequence..."
    )

    video = ImageSequenceClip(
        all_frames,
        fps=FPS
    )

    # ========================================================
    # ATTACH AUDIO
    # ========================================================

    video = video.with_audio(
        audio
    )

    # ========================================================
    # EXPORT
    # ========================================================

    print()
    print(
        "Rendering final MP4..."
    )

    video.write_videofile(
        output_video,
        fps=FPS,
        codec="libx264",
        audio_codec="aac"
    )

    # ========================================================
    # CLEANUP
    # ========================================================

    audio.close()

    video.close()

    print()

    print(
        "================================"
    )

    print(
        "VIDEO CREATED SUCCESSFULLY"
    )

    print(
        "================================"
    )

    print(
        output_video
    )