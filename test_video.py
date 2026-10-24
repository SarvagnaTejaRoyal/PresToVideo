import re
from pathlib import Path

from app.video_generator import create_video


# Release folder
release_dir = Path("output/release_2313663")

# Telugu translation file
translation_file = release_dir / "translations" / "telugu.txt"

# Telugu audio file
audio_file = release_dir / "audio" / "telugu.mp3"

# Output video
output_video = release_dir / "video" / "telugu.mp4"


# Read Telugu translation
translation_content = translation_file.read_text(
    encoding="utf-8"
)


# Extract numbered translation lines
summary_lines = []

for line in translation_content.splitlines():
    line = line.strip()

    match = re.match(r"^\d+\.\s*(.*)", line)

    if match:
        summary_lines.append(match.group(1).strip())


# Combine Telugu sentences
summary = " ".join(summary_lines)


print("\nTelugu text being sent to video generator:")
print(summary)


# Create video
print("\nCreating Telugu AI news video...")

create_video(
    title="72nd National Film Awards",
    summary_text=summary,
    audio_file=str(audio_file),
    output_video=str(output_video)
)

print("\nTELUGU VIDEO CREATED SUCCESSFULLY")
print(f"Video: {output_video}")