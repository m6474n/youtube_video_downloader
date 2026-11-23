#!/usr/bin/env python3
"""
YouTube Stream & Video Clips Downloader (High-Speed Direct Stream Edition)
Resolves direct video/audio stream URLs ONCE at startup and cuts exact clips
directly via FFmpeg byte-range HTTP streaming. Zero repeated manifest downloads.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import yt_dlp

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/Downloads")


def _ffmpeg_path() -> str:
    """Find ffmpeg binary in PATH or fallback to imageio_ffmpeg."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        src = imageio_ffmpeg.get_ffmpeg_exe()
        dst = os.path.join(SCRIPT_DIR, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
        return dst
    except Exception:
        return "ffmpeg"


def _js_runtimes() -> dict:
    """Auto-detect available JavaScript runtimes for yt-dlp."""
    runtimes = {}
    for name in ["deno", "node", "bun", "quickjs"]:
        path = shutil.which(name)
        if path:
            runtimes[name] = {"path": path}
    return runtimes


def parse_time_to_seconds(val) -> float:
    """Convert 'HH:MM:SS', 'MM:SS', or raw seconds to float seconds."""
    if isinstance(val, (int, float)):
        return float(val)
    val = str(val).strip()
    parts = val.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError:
        pass
    raise ValueError(f"Invalid timestamp format: '{val}'. Expected 'HH:MM:SS', 'MM:SS', or seconds.")


def format_seconds(sec: float) -> str:
    """Format seconds into HH:MM:SS string."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def load_config(config_path: str = None) -> dict:
    """Locate and load clips config from .js or .json file."""
    search_paths = []
    if config_path:
        search_paths.append(os.path.abspath(config_path))
    else:
        cwd = os.getcwd()
        search_paths.extend([
            os.path.join(cwd, "clips_config.js"),
            os.path.join(cwd, "clips_config.json"),
            os.path.join(SCRIPT_DIR, "clips_config.js"),
            os.path.join(SCRIPT_DIR, "clips_config.json"),
        ])

    target = None
    for p in search_paths:
        if os.path.exists(p):
            target = p
            break

    if not target:
        raise FileNotFoundError(
            f"Config file not found. Checked:\n" + "\n".join(f" - {p}" for p in search_paths)
        )

    print(f"📄 Loaded config: {target}")

    if target.endswith(".js"):
        node_exe = shutil.which("node")
        if node_exe:
            cmd = [
                node_exe,
                "-e",
                f"console.log(JSON.stringify(require({json.dumps(target)})))",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout)
        else:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            content = re.sub(r"^\s*(module\.exports\s*=|export\s+default)\s*", "", content, flags=re.MULTILINE)
            content = content.rstrip(";\n ")
            return json.loads(content)

    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


def sanitize_filename(name: str) -> str:
    """Replace illegal characters in filenames."""
    return re.sub(r'[\\/*?:"<>| ]', "_", name)


def resolve_stream_urls(url: str, quality: str):
    """
    Extract video information and direct CDN URLs ONCE.
    Avoids repeatedly querying YouTube API and downloading manifests.
    """
    runtimes = _js_runtimes()
    opts = {
        "remote_components": ["ejs:github"],
        "quiet": True,
        "no_warnings": True,
    }
    if runtimes:
        opts["js_runtimes"] = runtimes

    print(f"⏳ Connecting to YouTube and extracting stream URLs once (takes ~20s) ...", flush=True)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats", [])

    max_height = 9999
    if quality == "1080p":
        max_height = 1080
    elif quality == "720p":
        max_height = 720
    elif quality == "480p":
        max_height = 480

    # Pick best video: prefer avc1 (H264) for maximum FFmpeg speed and compatibility
    v_chosen = None
    for f in formats:
        h = f.get("height") or 0
        vcodec = f.get("vcodec") or ""
        proto = f.get("protocol") or ""
        if vcodec != "none" and vcodec.startswith("avc1") and proto == "https" and h <= max_height:
            if not v_chosen or h > (v_chosen.get("height") or 0):
                v_chosen = f

    # Fallback to any video <= max_height if avc1 not available
    if not v_chosen:
        for f in formats:
            h = f.get("height") or 0
            vcodec = f.get("vcodec") or ""
            proto = f.get("protocol") or ""
            if vcodec != "none" and proto == "https" and h <= max_height:
                if not v_chosen or h > (v_chosen.get("height") or 0):
                    v_chosen = f

    # Pick best audio
    a_chosen = None
    for f in formats:
        acodec = f.get("acodec") or ""
        vcodec = f.get("vcodec") or "none"
        proto = f.get("protocol") or ""
        tbr = f.get("tbr") or 0
        if acodec != "none" and vcodec == "none" and proto == "https":
            if not a_chosen or tbr > (a_chosen.get("tbr") or 0):
                a_chosen = f

    return info, v_chosen, a_chosen


def cut_clip(video_f: dict, audio_f: dict, clip_info: dict, idx: int, total: int, quality: str, output_dir: str):
    """Cut an exact clip directly via FFmpeg using input-seeking byte range streaming."""
    name = clip_info.get("name") or clip_info.get("title") or f"clip_{idx:02d}"
    start_sec = parse_time_to_seconds(clip_info["start"])
    end_sec = parse_time_to_seconds(clip_info["end"])
    duration = end_sec - start_sec

    if duration <= 0:
        print(f"⚠️ Skipping clip {idx}/{total} '{name}': End time must be greater than start time.")
        return False

    clean_clip_name = sanitize_filename(name)
    is_audio = quality == "audio"
    ext = "mp3" if is_audio else "mp4"

    # Exact title from config only
    filename = f"{clean_clip_name}.{ext}"
    output_path = os.path.join(output_dir, filename)

    print(f"\n🎬 [{idx}/{total}] Clip: '{filename}'")
    print(f"   ⏱  Range  : {format_seconds(start_sec)} ➔ {format_seconds(end_sec)} (Duration: {format_seconds(duration)})")
    print(f"   📁 Target : {output_path}")

    # Resume protection: skip already downloaded clips
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        print(f"   ⏭️ Already downloaded. Skipping: '{filename}'")
        return True

    ff = _ffmpeg_path()
    start_s = str(start_sec)
    dur_s = str(duration)

    cmd = [ff, "-y", "-nostdin", "-loglevel", "error", "-progress", "pipe:1"]

    if is_audio:
        cmd.extend(["-ss", start_s, "-t", dur_s, "-i", audio_f["url"]])
        cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k", output_path])
    else:
        # Input seeking: downloads ONLY requested byte range from YouTube CDN
        cmd.extend(["-ss", start_s, "-t", dur_s, "-i", video_f["url"]])
        cmd.extend(["-ss", start_s, "-t", dur_s, "-i", audio_f["url"]])
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "17",  # Visually lossless high quality
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ])

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    # Live progress bar parsing FFmpeg progress pipe
    dur_us = duration * 1_000_000
    for line in proc.stdout:
        line = line.strip()
        if line.startswith("out_time_us="):
            try:
                us = int(line.split("=")[1])
                pct = min(100.0, (us / dur_us) * 100)
                filled = int(24 * pct / 100)
                bar = "█" * filled + "░" * (24 - filled)
                curr_s = us / 1_000_000
                sys.stdout.write(
                    f"\r   [{bar}] {pct:5.1f}% | {format_seconds(curr_s)} / {format_seconds(duration)}  "
                )
                sys.stdout.flush()
            except Exception:
                pass
        elif line.startswith("progress=end"):
            break

    proc.wait()
    _, stderr = proc.communicate()

    if proc.returncode != 0:
        print(f"\n❌ Error cutting clip: {stderr.strip()[-300:]}")
        return False

    bar = "█" * 24
    sys.stdout.write(f"\r   [{bar}] 100.0% | Done!                                     \n")
    sys.stdout.flush()
    print(f"   ✅ Saved: {output_path}")
    return True


def main():
    print("=" * 60)
    print("   YouTube Stream & Video Clips Downloader (Fast Mode)")
    print("=" * 60)

    runtimes = _js_runtimes()
    runtime_str = ", ".join(runtimes.keys()) if runtimes else "None detected"
    print(f"🔧 JS runtime: {runtime_str}")

    config_arg = sys.argv[1].strip() if len(sys.argv) > 1 else None
    try:
        config = load_config(config_arg)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        sys.exit(1)

    url = config.get("url", "").strip()
    if not url or "VIDEO_ID" in url:
        print("❌ Error: Valid 'url' is required in clips_config.")
        sys.exit(1)

    clips = config.get("clips", [])
    if not clips:
        print("❌ Error: No clips found in 'clips' array.")
        sys.exit(1)

    quality = config.get("quality", "best")
    output_dir = os.path.expanduser(os.path.expandvars(config.get("output_dir") or DEFAULT_OUTPUT_DIR))
    os.makedirs(output_dir, exist_ok=True)

    try:
        info, video_f, audio_f = resolve_stream_urls(url, quality)
    except Exception as e:
        print(f"❌ Failed to fetch stream URLs: {e}")
        sys.exit(1)

    video_title = info.get("title", "video")
    duration_str = info.get("duration_string", "N/A")
    res_str = f"{video_f.get('height')}p" if video_f else "Audio only"

    print(f"\n📹 Video    : {video_title}")
    print(f"⏱  Duration : {duration_str}")
    print(f"🎯 Quality  : {res_str} (H.264 / CRF 17 High Quality)")
    print(f"✂️  Clips    : {len(clips)} queued")
    print(f"📁 Dest     : {output_dir}")

    success_count = 0
    total = len(clips)
    for idx, clip in enumerate(clips, 1):
        try:
            if cut_clip(video_f, audio_f, clip, idx, total, quality, output_dir):
                success_count += 1
        except Exception as e:
            print(f"❌ Failed clip {idx}/{total} ({clip.get('name', 'unnamed')}): {e}")

    print("\n" + "=" * 60)
    print(f"✨ Completed: {success_count}/{total} clips downloaded successfully.")
    print(f"📁 Folder: {os.path.abspath(output_dir)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
