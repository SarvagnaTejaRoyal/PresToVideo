import streamlit as st
from app.pib_scraper import list_releases
from app.pipeline import generate_video_for_release


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PIB Press Release to Video",
    page_icon="🎥",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("🎥 PIB Press Release to Video")

st.write(
    "Select a date, choose a PIB press release, "
    "select a language, and generate an AI news video."
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Video Settings")

language = st.sidebar.selectbox(
    "Select Language",
    [
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
        "Odia",
        "Bengali",
        "Assamese",
        "Manipuri"
    ]
)


# ============================================================
# DATE SELECTION
# ============================================================

st.subheader("📅 Select Press Release Date")

selected_date = st.date_input(
    "Choose a date",
    value=None,
    max_value=None
)


# ============================================================
# RELEASE STATE
# ============================================================

if "releases" not in st.session_state:
    st.session_state.releases = []

if "selected_date" not in st.session_state:
    st.session_state.selected_date = None


# ============================================================
# FETCH RELEASES
# ============================================================

if st.button("🔄 Fetch Releases"):

    if selected_date is None:

        st.warning(
            "Please select a date first."
        )

    else:

        with st.spinner(
            f"Fetching PIB releases for "
            f"{selected_date.strftime('%d-%B-%Y')}..."
        ):

            try:

                releases = list_releases(
                    selected_date=selected_date
                )

                st.session_state.releases = releases
                st.session_state.selected_date = selected_date
                st.session_state.pop("generated_video", None)

                if releases:

                    st.success(
                        f"{len(releases)} releases found for "
                        f"{selected_date.strftime('%d-%B-%Y')}."
                    )

                else:

                    st.warning(
                        f"No PIB releases were found for "
                        f"{selected_date.strftime('%d-%B-%Y')}."
                    )

            except Exception as e:

                st.session_state.releases = []

                st.error(
                    f"Failed to fetch PIB releases: {e}"
                )


# ============================================================
# RELEASE SELECTION
# ============================================================

if st.session_state.releases:

    st.subheader("📰 Select Press Release")

    release_options = {
        release.title: release.prid
        for release in st.session_state.releases
    }

    selected_title = st.selectbox(
        "Choose a press release",
        list(release_options.keys())
    )

    selected_prid = release_options[
        selected_title
    ]

    st.write(
        f"**PRID:** {selected_prid}"
    )

    st.write(
        f"**Date:** "
        f"{st.session_state.selected_date.strftime('%d-%B-%Y')}"
    )


# ============================================================
# GENERATE VIDEO
# ============================================================

    if st.button("🎬 Generate Video"):

        with st.spinner(
            "Generating video... "
            "This may take some time."
        ):

            try:

                result = generate_video_for_release(
                    prid=selected_prid,
                    language=language
                )

                if result["status"] == "SUCCESS":

                    st.session_state.generated_video = (
                        result["video_file"]
                    )

                    st.success(
                        "Video generated successfully!"
                    )

                else:

                    st.error(
                        f"Video generation failed "
                        f"during {result.get('stage', 'unknown')} stage."
                    )

                    if result.get("error"):
                        st.error(
                            result["error"]
                        )

            except Exception as e:

                st.error(
                    f"Failed to generate video: {e}"
                )


# ============================================================
# VIDEO DISPLAY
# ============================================================

if "generated_video" in st.session_state:

    st.subheader("🎥 Generated Video")

    video_file = st.session_state.generated_video

    st.video(video_file)

    st.success(
        "Your PIB video is ready!"
    )

else:

    st.info(
        "Your generated video will appear here "
        "after you click 'Generate Video'."
    )