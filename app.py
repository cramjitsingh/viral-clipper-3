import streamlit as st
import subprocess, os, re, random, urllib.parse, json, glob

st.set_page_config(page_title="Viral Clipper", page_icon="✂️")
st.title("✂️ Viral Clipper")
st.write("Paste a YouTube link, get short clips with captions + virality score.")

url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")
clip_len = st.slider("Clip length (seconds)", 15, 60, 30)
num_clips = st.slider("How many clips?", 1, 5, 3)
want_captions = st.checkbox("Burn-in Captions (if available)", value=True)

def virality_score(clip_path, position):
    # Simple but real signal: loudness = energy, early clips = better hook
    try:
        r = subprocess.run(["ffmpeg","-i",clip_path,"-vn","-af","volumedetect","-f","null","/dev/null"],
            stderr=subprocess.PIPE, text=True)
        m = re.search(r"mean_volume: ([\-\d\.]+)", r.stderr)
        vol = float(m.group(1)) if m else -25.0
        # -30 quiet -> -10 loud
        energy = max(0, min(100, (vol + 30) * 3.5))
    except:
        energy = 50
    hook = max(0, 100 - position * 12)  # earlier = stronger hook
    score = int(energy * 0.6 + hook * 0.4 + random.randint(-5, 5))
    return max(5, min(98, score))

def get_subtitle_file(video_id):
    # Look for any .vtt downloaded by yt-dlp
    files = glob.glob(f"*.{video_id}*.vtt") + glob.glob("*.vtt")
    return files[0] if files else None

if st.button("Make Clips"):
    if not url:
        st.warning("Paste a YouTube link first.")
        st.stop()
    with st.spinner("Downloading + cutting... this takes 1-2 mins"):
        # Clean old files
        for f in glob.glob("*.mp4")+glob.glob("*.vtt")+glob.glob("*.srt"):
            try: os.remove(f)
            except: pass

        # Download with subtitles + android client (less blocking)
        ydl_cmd = [
            "yt-dlp",
            "--impersonate", "chrome",
            "--extractor-args", "youtube:player_client=android,web",
            "-f", "best[height<=720][ext=mp4]/best[height<=720]/best",
            "--write-auto-subs", "--sub-langs", "en.*",
            "--convert-subs", "srt",
            "-o", "full.%(ext)s",
            url
        ]
        res = subprocess.run(ydl_cmd, capture_output=True, text=True)
        if not os.path.exists("full.mp4"):
            st.error("Could not download video. Try a different link.")
            st.code(res.stderr[-1000:])
            st.stop()

        # Get duration
        probe = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1","full.mp4"], capture_output=True, text=True)
        try: duration = float(probe.stdout.strip())
        except: duration = 180

        sub = get_subtitle_file("full")
        st.info(f"Video length: {int(duration)}s | Captions found: {'Yes ✅' if sub else 'No - will make clips without captions'}")

        for i in range(num_clips):
            start = int((duration / (num_clips + 1)) * (i + 1))
            out = f"clip_{i+1}.mp4"
            # Burn captions if we have them
            if want_captions and sub:
                vf = f"subtitles='{sub}':force_style='FontSize=22,PrimaryColour=&HFFFFFF&,OutlineColour=&H80000000&,BorderStyle=1',scale=720:-2,format=yuv420p"
            else:
                vf = "scale=720:-2,format=yuv420p"
            subprocess.run(["ffmpeg","-y","-ss",str(start),"-i","full.mp4","-t",str(clip_len),"-vf",vf,"-c:a","aac",out], capture_output=True)

            if os.path.exists(out):
                score = virality_score(out, i)
                color = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
                st.subheader(f"Clip {i+1} {color} Virality Score: {score}/100")
                st.video(out)
                with open(out, "rb") as f:
                    st.download_button(f"⬇️ Download Clip {i+1}", f, file_name=out, mime="video/mp4", key=f"dl{i}")

                # Share / Post buttons
                st.write("**Post / Share:**")
                c1, c2, c3, c4 = st.columns(4)
                # These open the app's upload/share screen - you pick the downloaded clip
                with c1: st.link_button("▶️ TikTok", "https://www.tiktok.com/upload")
                with c2: st.link_button("📸 Instagram", "https://www.instagram.com/reels/create/")
                with c3: st.link_button("▶️ YouTube", "https://www.youtube.com/upload")
                with c4: st.link_button("👍 Facebook", "https://www.facebook.com/reels/create/")
                st.caption("Tip: Download clip first, then tap a button above, then upload it in that app.")
                st.divider()
