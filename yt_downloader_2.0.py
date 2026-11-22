#!/usr/bin/env python3
"""
YouTube Video Downloader 2.0
Fetches all available resolutions and lets you pick one.
Requires: pip install yt-dlp
"""

import os
import shutil
import sys
import yt_dlp

DEFAULT_OUTPUT_DIR = "downloads"


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
    Enables JS runtimes and the remote EJS challenge solver.
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
    return opts


def get_formats(url: str):
    """Fetch and return all available video+audio formats."""
    ydl_opts = {
        **_common_ydl_opts(),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    print(f"\n📹 {info.get('title')}")
    print(f"⏱  {info.get('duration_string', 'N/A')}  |  👁  {info.get('view_count', 0):,} views\n")

    formats = info.get("formats", [])

    # Collect unique video resolutions (with video stream)
    seen = {}
    for f in formats:
        height = f.get("height")
        ext    = f.get("ext", "")
        vcodec = f.get("vcodec", "none") or "none"
        acodec = f.get("acodec", "none") or "none"
        fps    = f.get("fps") or 0
        tbr    = f.get("tbr") or 0

        if not height or vcodec == "none":
            continue

        key = height
        # Prefer higher bitrate at same resolution
        existing = seen.get(key)
        if not existing or tbr > (existing.get("tbr") or 0):
            seen[key] = {
                "format_id": f["format_id"],
                "height":    height,
                "ext":       ext,
                "fps":       int(fps),
                "tbr":       tbr,
                "vcodec":    vcodec,
                "acodec":    acodec,
                "filesize":  f.get("filesize") or f.get("filesize_approx"),
            }

    # Sort highest to lowest
    sorted_res = sorted(seen.values(), key=lambda x: x["height"], reverse=True)
    return sorted_res, info


def format_size(size):
    if not size:
        return "size unknown"
    if size >= 1_000_000_000:
        return f"{size/1_000_000_000:.1f} GB"
    if size >= 1_000_000:
        return f"{size/1_000_000:.1f} MB"
    return f"{size/1_000:.0f} KB"


def pick_format(sorted_res):
    """Print resolution table and let user pick one."""
    print("Available resolutions:")
    print(f"  {'#':<4} {'Resolution':<12} {'FPS':<6} {'Ext':<6} {'Size':<12}")
    print("  " + "-" * 42)

    for i, f in enumerate(sorted_res, 1):
        size_str = format_size(f["filesize"])
        fps_str  = f"{f['fps']}fps" if f["fps"] else "—"
        print(f"  {i:<4} {str(f['height'])+'p':<12} {fps_str:<6} {f['ext']:<6} {size_str:<12}")

    # Audio-only option at the bottom
    print(f"  {len(sorted_res)+1:<4} {'Audio only':<12} {'—':<6} {'mp3':<6} {'—':<12}")

    print()
    while True:
        choice = input(f"Pick a number [1-{len(sorted_res)+1}]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(sorted_res) + 1:
            return int(choice)
        print("  Invalid choice, try again.")


def progress_hook(d):
    if d["status"] == "downloading":
        pct   = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "—").strip()
        eta   = d.get("_eta_str", "—").strip()
        print(f"\r  {pct:<8} speed: {speed:<12} ETA: {eta}    ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r  ✅ Done — merging/processing …                     ")


def download(url, choice, sorted_res, output_dir=DEFAULT_OUTPUT_DIR):
    output_dir = os.path.expanduser(os.path.expandvars(output_dir))
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    is_audio = choice == len(sorted_res) + 1

    common_opts = {
        **_common_ydl_opts(),
        "outtmpl": output_template,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
    }

    if is_audio:
        ydl_opts = {
            **common_opts,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        selected = sorted_res[choice - 1]
        height   = selected["height"]
        # Best video at this exact height + best audio, merged to mp4
        fmt = f"bestvideo[height={height}]+bestaudio/best[height<={height}]"
        ydl_opts = {
            **common_opts,
            "format": fmt,
            "merge_output_format": "mp4",
            "postprocessors": [],
        }

    label = "audio (mp3)" if is_audio else f"{sorted_res[choice-1]['height']}p"
    print(f"\n⬇  Downloading {label} …\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print(f"\n📁 Saved to: {os.path.abspath(output_dir)}\n")


def main():
    print("=" * 52)
    print("   YouTube Downloader  —  all resolutions")
    print("=" * 52)

    # Show detected JS runtime
    runtimes = _js_runtimes()
    runtime_str = ", ".join(runtimes.keys()) if runtimes else "None detected"
    print(f"🔧 JS runtime : {runtime_str}")

    url = sys.argv[1].strip() if len(sys.argv) > 1 else input("\nPaste YouTube link: ").strip()

    if not url:
        print("❌ No URL provided.")
        sys.exit(1)

    try:
        sorted_res, info = get_formats(url)
    except Exception as e:
        print(f"❌ Could not fetch formats: {e}")
        sys.exit(1)

    if not sorted_res:
        print("❌ No downloadable video formats found.")
        sys.exit(1)

    choice     = pick_format(sorted_res)
    output_dir = input(f"Save folder [Enter = '{DEFAULT_OUTPUT_DIR}']: ").strip() or DEFAULT_OUTPUT_DIR

    try:
        download(url, choice, sorted_res, output_dir)
    except yt_dlp.utils.DownloadError as e:
        print(f"\n❌ Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
