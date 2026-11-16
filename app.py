import streamlit as st
import subprocess
import os
import glob

st.set_page_config(page_title="Viral Clipper", page_icon="✂️")
st.title("✂️ Viral Clipper")
st.write("Paste a YouTube link, get short clips.")

url = st.text_input("YouTube URL")
duration = st.slider("Clip length (seconds)", 15, 60, 30)
num_clips = st.slider("How many clips?", 1, 5, 3)

if st.button("Make Clips") and url:
    with st.spinner("Downloading and clipping... this can take 1-2 mins"):
        os.makedirs("output", exist_ok=True)
        for f in glob.glob("output/*"):
            os.remove(f)
        # Download best mp4
        subprocess.run(["yt-dlp", "-f", "mp4", "-o", "input.mp4", url], check=False)
        if not os.path.exists("input.mp4"):
            st.error("Could not download video. Try a different link.")
        else:
            # Get duration
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "input.mp4"], capture_output=True, text=True)
            try:
                total = float(probe.stdout.strip())
            except:
                total = 120
            import random
            for i in range(num_clips):
                start = random.randint(0, max(0, int(total - duration - 1)))
                out = f"output/clip_{i+1}.mp4"
                subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-i", "input.mp4", "-t", str(duration), "-c", "copy", out], capture_output=True)
            st.success("Done!")
            for f in sorted(glob.glob("output/*.mp4")):
                st.video(f)
                with open(f, "rb") as file:
                    st.download_button(f"Download {os.path.basename(f)}", file, file_name=os.path.basename(f))
