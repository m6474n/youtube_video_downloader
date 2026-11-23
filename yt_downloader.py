#!/usr/bin/env python3
"""
YouTube Video Downloader
Paste any YouTube share link and download in your preferred quality.
Requires: pip install yt-dlp
"""

import os
import shutil
import sys
import yt_dlp

DEFAULT_OUTPUT_DIR = os.path.expanduser("~/Downloads")


def _ffmpeg_path() -> str | None:
    """Find ffmpeg in PATH or fallback to imageio_ffmpeg."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _js_runtimes() -> dict:
    """
    Auto-detect available JavaScript runtimes for yt-dlp.
    yt-dlp requires a JS runtime (Node, Deno, Bun, QuickJS) to solve
    YouTube's player and signature challenges.
    Returns a dict like {'node': {'path': '/usr/local/bin/node'}}.
    """
    runtimes = {}
    for name in ["deno", "node", "bun", "quickjs"]:
        path = shutil.which(name)
        if path:
            runtimes[name] = {"path": path}
    return runtimes


def _common_ydl_opts() -> dict:
    """
    Base configuration for yt-dlp to avoid HTTP 403 Forbidden.
    Enables JS runtimes, remote EJS challenge solver, and ffmpeg.
    """
    opts = {
        "remote_components": ["ejs:github"],
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 5,
        "retry_sleep_functions": {"http": lambda n: 2 ** n},
    }
    runtimes = _js_runtimes()
    if runtimes:
        opts["js_runtimes"] = runtimes
    ff = _ffmpeg_path()
    if ff:
        opts["ffmpeg_location"] = ff
    return opts


def list_formats(url: str):
    """Show available formats for the video."""
    ydl_opts = {
        **_common_ydl_opts(),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print(f"\n📹 Title : {info.get('title')}")
        print(f"⏱  Duration: {info.get('duration_string', 'N/A')}")
        print(f"👁  Views  : {info.get('view_count', 'N/A'):,}\n")
    return info


def download_video(url: str, quality: str = "best", output_dir: str = DEFAULT_OUTPUT_DIR):
    """
    Download a YouTube video.

    quality options:
      best       → maximum resolution available (default)
      1080p      → up to 1080p
      720p       → up to 720p
      480p       → up to 480p
      audio      → audio only (mp3)
    """
    # Expand user directory (e.g. ~/Downloads)
    output_dir = os.path.expanduser(os.path.expandvars(output_dir))
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    format_map = {
        "best":  "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "audio": "bestaudio/best",
    }

    fmt = format_map.get(quality, format_map["best"])

    ydl_opts = {
        **_common_ydl_opts(),
        "format": fmt,
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        "postprocessors": [],
    }

    # Audio-only: convert to mp3
    if quality == "audio":
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
        ydl_opts["outtmpl"] = os.path.join(output_dir, "%(title)s.%(ext)s")

    print(f"\n⬇  Downloading ({quality}) …\n")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print(f"\n✅ Saved to: {os.path.abspath(output_dir)}")


def progress_hook(d):
    if d["status"] == "downloading":
        pct   = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        eta   = d.get("_eta_str", "").strip()
        print(f"\r  {pct}  speed: {speed}  ETA: {eta}    ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r  100%  — processing file …          ")


def pick_quality() -> str:
    options = {
        "1": "best",
        "2": "1080p",
        "3": "720p",
        "4": "480p",
        "5": "audio",
    }
    print("\nSelect quality:")
    print("  1) Best available (default)")
    print("  2) 1080p")
    print("  3) 720p")
    print("  4) 480p")
    print("  5) Audio only (MP3)")
    choice = input("\nEnter choice [1-5] (press Enter for best): ").strip() or "1"
    return options.get(choice, "best")


def main():
    print("=" * 50)
    print("   YouTube Downloader — powered by yt-dlp")
    print("=" * 50)

    # Show detected JS runtimes
    runtimes = _js_runtimes()
    runtime_str = ", ".join(runtimes.keys()) if runtimes else "None detected"
    print(f"🔧 JS runtime : {runtime_str}")

    # Accept URL from CLI arg or prompt
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = input("\nPaste YouTube link: ").strip()

    if not url:
        print("❌ No URL provided.")
        sys.exit(1)

    try:
        list_formats(url)
    except Exception as e:
        print(f"❌ Could not fetch video info: {e}")
        sys.exit(1)

    quality    = pick_quality()
    output_dir = input("Save to folder [press Enter for '~/Downloads']: ").strip() or DEFAULT_OUTPUT_DIR

    try:
        download_video(url, quality=quality, output_dir=output_dir)
    except yt_dlp.utils.DownloadError as e:
        print(f"\n❌ Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
