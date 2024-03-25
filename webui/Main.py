import streamlit as st

st.set_page_config(page_title="ASONAI", page_icon="🤖", layout="wide",
                   initial_sidebar_state="auto")
import sys
import os
from uuid import uuid4

from loguru import logger
from app.models.schema import VideoParams, VideoAspect, VoiceNames, VideoConcatMode
from app.services import task as tm, llm

os.system("cat /etc/ImageMagick-6/policy.xml | sed 's/none/read,write/g'> /etc/ImageMagick-6/policy.xml")

# Hiding Streamlit style
hide_streamlit_style = """
<style>#root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.title("MoneyPrinterTurbo")
st.write(
)

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
font_dir = os.path.join(root_dir, "resource", "fonts")
song_dir = os.path.join(root_dir, "resource", "songs")

# st.session_state

if 'video_subject' not in st.session_state:
    st.session_state['video_subject'] = ''
if 'video_script' not in st.session_state:
    st.session_state['video_script'] = ''
if 'video_terms' not in st.session_state:
    st.session_state['video_terms'] = ''


def get_all_fonts():
    fonts = []
    for root, dirs, files in os.walk(font_dir):
        for file in files:
            if file.endswith(".ttf") or file.endswith(".ttc"):
                fonts.append(file)
    return fonts


def get_all_songs():
    songs = []
    for root, dirs, files in os.walk(song_dir):
        for file in files:
            if file.endswith(".mp3"):
                songs.append(file)
    return songs


def init_log():
    logger.remove()
    _lvl = "DEBUG"

    def format_record(record):
        # Get the full path of the file in the log record
        file_path = record["file"].path
        # Convert the absolute path to a relative path from the project root directory
        relative_path = os.path.relpath(file_path, root_dir)
        # Update the file path in the record
        record["file"].path = f"./{relative_path}"
        # Here you can adjust the format as needed
        record['message'] = record['message'].replace(root_dir, ".")

        _format = '<green>{time:%Y-%m-%d %H:%M:%S}</> | ' + \
                  '<level>{level}</> | ' + \
                  '"{file.path}:{line}":<blue> {function}</> ' + \
                  '- <level>{message}</>' + "\n"
        return _format

    logger.add(
        sys.stdout,
        level=_lvl,
        format=format_record,
        colorize=True,
    )


init_log()

panel = st.columns(3)
left_panel = panel[0]
middle_panel = panel[1]
right_panel = panel[2]

# Define cfg as VideoParams class
cfg = VideoParams()

with left_panel:
    with st.container(border=True):
        st.write("**Copywriting Settings**")
        cfg.video_subject = st.text_input("Video Topic (Provide a keyword, AI will generate video copy)",
                                          value=st.session_state['video_subject']).strip()
        if st.button("Click to generate 【Video Copy】 and 【Video Keywords】 based on **Topic**", key="auto_generate_script"):
            with st.spinner("AI is generating video copy and keywords..."):
                script = llm.generate_script(cfg.video_subject)
                terms = llm.generate_terms(cfg.video_subject, script)
                st.toast('AI generation successful')
                st.session_state['video_script'] = script
                st.session_state['video_terms'] = ", ".join(terms)

        cfg.video_script = st.text_area(
            "Video Copy (Blue[①Can leave blank, AI will generate ②Use punctuation properly, helps in generating subtitles])",
            value=st.session_state['video_script'],
            height=280
        )
        if st.button("Click to generate【Video Keywords】based on **Copy**", key="auto_generate_terms"):
            if not cfg.video_script:
                st.error("Please enter video copy first")
                st.stop()

            with st.spinner("AI is generating video keywords..."):
                terms = llm.generate_terms(cfg.video_subject, cfg.video_script)
                st.toast('AI generation successful')
                st.session_state['video_terms'] = ", ".join(terms)

        cfg.video_terms = st.text_area(
            "Video Keywords (Blue[①Can leave blank, AI will generate ②Separate with **English commas**, supports only English])",
            value=st.session_state['video_terms'],
            height=50)

with middle_panel:
    with st.container(border=True):
        st.write("**Video Settings**")
        video_concat_modes = [
            ("Sequential Concatenation", "sequential"),
            ("Random Concatenation (Recommended)", "random"),
        ]
        selected_index = st.selectbox("Video Concatenation Mode",
                                      index=1,
                                      options=range(len(video_concat_modes)),  # Use index as internal option value
                                      format_func=lambda x: video_concat_modes[x][0]  # Display label to user
                                      )
        cfg.video_concat_mode = VideoConcatMode(video_concat_modes[selected_index][1])

        video_aspect_ratios = [
            ("Portrait 9:16 (TikTok Video)", VideoAspect.portrait.value),
            ("Landscape 16:9 (Watermelon Video)", VideoAspect.landscape.value),
            # ("Square 1:1", VideoAspect.square.value)
        ]
        selected_index = st.selectbox("Video Aspect Ratio",
                                      options=range(len(video_aspect_ratios)),  # Use index as internal option value
                                      format_func=lambda x: video_aspect_ratios[x][0]  # Display label to user
                                      )
        cfg.video_aspect = VideoAspect(video_aspect_ratios[selected_index][1])

        cfg.video_clip_duration = st.selectbox("Maximum Duration of Video Clips (seconds)", options=[2, 3, 4, 5, 6], index=1)
        cfg.video_count = st.selectbox("Number of Videos to Generate at Once", options=[1, 2, 3, 4, 5], index=0)
    with st.container(border=True):
        st.write("**Audio Settings**")
        # Create a mapping dictionary to map original values to friendly names
        friendly_names = {
            voice: voice.
            replace("female", "Female").
            replace("male", "Male").
            replace("zh-CN", "Chinese").
            replace("zh-HK", "Hong Kong").
            replace("zh-TW", "Taiwan").
            replace("en-US", "English").
            replace("Neural", "") for
            voice in VoiceNames}
        selected_friendly_name = st.selectbox("Voice", options=list(friendly_names.values()))
        voice_name = list(friendly_names.keys())[list(friendly_names.values()).index(selected_friendly_name)]
        cfg.voice_name = voice_name

        bgm_options = [
            ("No Background Music", ""),
            ("Random Background Music", "random"),
            ("Custom Background Music", "custom"),
        ]
        selected_index = st.selectbox("Background Music",
                                      index=1,
                                      options=range(len(bgm_options)),  # Use index as internal option value
                                      format_func=lambda x: bgm_options[x][0]  # Display label to user
                                      )
        # Get the selected background music type
        bgm_type = bgm_options[selected_index][1]

        # Show or hide components based on selection
        if bgm_type == "custom":
            custom_bgm_file = st.text_input("Enter the file path for custom background music:")
            if custom_bgm_file and os.path.exists(custom_bgm_file):
                cfg.bgm_file = custom_bgm_file
                # st.write(f":red[Custom background music selected]：**{custom_bgm_file}**")
        cfg.bgm_volume = st.selectbox("Background Music Volume (0.2 means 20%, background sound should not be too loud)",
                                      options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], index=2)

with right_panel:
    with st.container(border=True):
        st.write("**Subtitle Settings**")
        cfg.subtitle_enabled = st.checkbox("Generate Subtitles (If unchecked, the settings below will not take effect)", value=True)
        font_names = get_all_fonts()
        cfg.font_name = st.selectbox("Font", font_names)

        subtitle_positions = [
            ("Top", "top"),
            ("Center", "center"),
            ("Bottom (Recommended)", "bottom"),
        ]
        selected_index = st.selectbox("Subtitle Position",
                                      index=2,
                                      options=range(len(subtitle_positions)),  # Use index as internal option value
                                      format_func=lambda x: subtitle_positions[x][0]  # Display label to user
                                      )
        cfg.subtitle_position = subtitle_positions[selected_index][1]

        font_cols = st.columns([0.3, 0.7])
        with font_cols[0]:
            cfg.text_fore_color = st.color_picker("Subtitle Color", "#FFFFFF")
        with font_cols[1]:
            cfg.font_size = st.slider("Subtitle Size", 30, 100, 60)

        stroke_cols = st.columns([0.3, 0.7])
        with stroke_cols[0]:
            cfg.stroke_color = st.color_picker("Stroke Color", "#000000")
        with stroke_cols[1]:
            cfg.stroke_width = st.slider("Stroke Width", 0.0, 10.0, 1.5)

start_button = st.button("Start Generating Video", use_container_width=True, type="primary")
if start_button:
    task_id = str(uuid4())
    if not cfg.video_subject and not cfg.video_script:
        st.error("Video Topic or Video Copy, both cannot be empty")
        st.stop()

    st.write(cfg)

    log_container = st.empty()

    log_records = []


    def log_received(msg):
        with log_container:
            log_records.append(msg)
            st.code("\n".join(log_records))


    logger.add(log_received)

    logger.info("Starting video generation")

    tm.start(task_id=task_id, params=cfg)