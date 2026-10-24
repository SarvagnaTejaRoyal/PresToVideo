from app.pipeline import generate_video_for_release


result = generate_video_for_release(
    prid="2313938",
    language="Telugu"
)

print("\nFINAL RESULT")
print("=" * 50)

print("PRID:", result["prid"])
print("Title:", result["title"])
print("Language:", result["language"])
print("Video:", result["video_file"])