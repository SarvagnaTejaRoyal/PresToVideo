from gtts import gTTS
from gtts.lang import tts_langs
import os


# ==========================================
# Output folder
# ==========================================

OUTPUT_FOLDER = "output/tts_test"

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ==========================================
# Languages to test
# ==========================================

languages = {
    "English": "en",
    "Hindi": "hi",
    "Urdu": "ur",
    "Punjabi": "pa",
    "Gujarati": "gu",
    "Marathi": "mr",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Tamil": "ta",
    "Odia": "or",
    "Bengali": "bn",
    "Assamese": "as",
    "Manipuri": "mni"
}


# ==========================================
# Short sample sentences
# ==========================================

sample_text = {

    "English":
        "The Government of India has announced a new initiative.",

    "Hindi":
        "भारत सरकार ने एक नई पहल की घोषणा की है।",

    "Urdu":
        "حکومت ہند نے ایک نئی پہل کا اعلان کیا ہے۔",

    "Punjabi":
        "ਭਾਰਤ ਸਰਕਾਰ ਨੇ ਇੱਕ ਨਵੀਂ ਪਹਿਲ ਦਾ ਐਲਾਨ ਕੀਤਾ ਹੈ।",

    "Gujarati":
        "ભારત સરકારે એક નવી પહેલની જાહેરાત કરી છે।",

    "Marathi":
        "भारत सरकारने एका नवीन उपक्रमाची घोषणा केली आहे।",

    "Telugu":
        "భారత ప్రభుత్వం ఒక కొత్త కార్యక్రమాన్ని ప్రకటించింది।",

    "Kannada":
        "ಭಾರತ ಸರ್ಕಾರವು ಹೊಸ ಯೋಜನೆಯನ್ನು ಘೋಷಿಸಿದೆ।",

    "Malayalam":
        "ഇന്ത്യാ സർക്കാർ ഒരു പുതിയ പദ്ധതി പ്രഖ്യാപിച്ചു.",

    "Tamil":
        "இந்திய அரசு ஒரு புதிய திட்டத்தை அறிவித்துள்ளது.",

    "Odia":
        "ଭାରତ ସରକାର ଏକ ନୂତନ ପଦକ୍ଷେପ ଘୋଷଣା କରିଛନ୍ତି।",

    "Bengali":
        "ভারত সরকার একটি নতুন উদ্যোগ ঘোষণা করেছে।",

    "Assamese":
        "ভাৰত চৰকাৰে এটা নতুন পদক্ষেপ ঘোষণা কৰিছে।",

    "Manipuri":
        "ভারত সরকারনা অমা অমা থৌরাং শেমজিনবা ঘোষণা তৌরে।"
}


# ==========================================
# Check gTTS supported languages
# ==========================================

print()
print("Checking gTTS language support...")
print()

supported_languages = tts_langs()


# ==========================================
# Test each language
# ==========================================

results = []


for language, code in languages.items():

    print("----------------------------------------")
    print(f"Testing: {language}")
    print(f"Code:    {code}")

    # --------------------------------------
    # Check whether gTTS knows the code
    # --------------------------------------

    if code not in supported_languages:

        print("STATUS: NOT SUPPORTED BY gTTS")

        results.append(
            (
                language,
                code,
                "NOT SUPPORTED"
            )
        )

        continue

    # --------------------------------------
    # Generate audio
    # --------------------------------------

    try:

        text = sample_text[language]

        output_file = os.path.join(
            OUTPUT_FOLDER,
            f"{code}_{language.lower()}.mp3"
        )

        tts = gTTS(
            text=text,
            lang=code,
            slow=False
        )

        tts.save(
            output_file
        )

        print("STATUS: SUCCESS")
        print(f"Audio: {output_file}")

        results.append(
            (
                language,
                code,
                "SUCCESS"
            )
        )

    except Exception as e:

        print("STATUS: FAILED")
        print(f"Error: {e}")

        results.append(
            (
                language,
                code,
                "FAILED"
            )
        )


# ==========================================
# Final report
# ==========================================

print()
print()
print("========================================")
print("TTS TEST SUMMARY")
print("========================================")

for language, code, status in results:

    print(
        f"{language:<12} "
        f"{code:<5} "
        f"{status}"
    )

print()
print(
    f"Audio files are saved in: "
    f"{OUTPUT_FOLDER}"
)