# YouTube Video Downloader 📹

A Python CLI tool powered by [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) to download YouTube videos in maximum resolution or extract high-quality MP3 audio with real-time progress tracking.

---

## ✨ Features

- **Quality Presets**: Quickly pick between Best Available, 1080p, 720p, 480p, or MP3 Audio.
- **Resolution Picker (v2.0)**: Inspect exact resolutions, FPS, codecs, and estimated file sizes in a formatted table before downloading.
- **Bypasses HTTP 403 Forbidden**: Configured with automated JavaScript challenge solving (`ejs:github` via Node.js/Deno/Bun) to overcome YouTube's player cipher restrictions.
- **Clean Merging**: Merges highest quality separate video + audio DASH streams into MP4 automatically.
- **Default Output Folder**: Automatically saves downloads to `~/Downloads` (user's system Downloads folder; can be overridden interactively).
- **Live Progress**: Displays download percentage, speed, and ETA.

---

## 📋 Prerequisites

1. **Python 3.8+**
2. **Node.js** (or Deno / Bun) — required by `yt-dlp` to execute YouTube's player challenges:
   ```bash
   # Windows (winget)
   winget install OpenJS.NodeJS
   # macOS (Homebrew)
   brew install node
   ```
3. **FFmpeg** — required to merge separate video and audio streams into MP4 and convert to MP3. Automatically provided via Python package `imageio-ffmpeg` in `requirements.txt`, or installed system-wide:
   ```bash
   # Windows (winget)
   winget install Gyan.FFmpeg
   # macOS (Homebrew)
   brew install ffmpeg
   ```

---

## 🚀 Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/youtube_video_downloader.git
cd youtube_video_downloader

pip install -r requirements.txt
```

*(Or simply run `pip install --upgrade yt-dlp`)*

---

## 💻 Usage

### Quick Shortcuts (Any terminal, anywhere)

- **Download Full Video**:
  ```bash
  download-video
  # or with direct link:
  download-video "https://www.youtube.com/watch?v=VIDEO_ID"
  ```

- **Download Stream / Video Clips Batch** (without downloading whole video):
  ```bash
  download-clips
  # or specify custom config file:
  download-clips ./path/to/my_clips.js
  ```

- **Open Clips Config in Antigravity IDE**:
  ```bash
  open-clipping-config
  ```

- **Open Project in Antigravity**:
  ```bash
  clipper
  ```

---

### Option 0: Multi-Clip Extractor (`yt_clips_downloader.py`)

Extract multiple exact time slices from long streams or 24-hour recordings without downloading the entire video.

1. Edit [clips_config.js](file:///d:/python_projects/youtube_video_downloader/clips_config.js):
   ```javascript
   module.exports = {
     url: "https://www.youtube.com/watch?v=VIDEO_ID",
     quality: "best", // "best", "1080p", "720p", "480p", "audio"
     output_dir: "~/Downloads",
     clips: [
       { name: "intro", start: "00:01:00", end: "00:02:30" },
       { name: "highlight", start: "01:15:20", end: "01:18:00" },
       { name: "outro", start: "23:45:00", end: "23:47:30" },
     ],
   };
   ```

2. Run:
   ```bash
   download-clips
   # or
   python yt_clips_downloader.py
   ```

### Option 1: Standard Downloader (`yt_downloader.py`)

Interactive prompt:
```bash
python3 yt_downloader.py
```

Pass video URL directly as an argument:
```bash
python3 yt_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Example session:
```text
==================================================
   YouTube Downloader — powered by yt-dlp
==================================================
🔧 JS runtime : node

📹 Title : Example YouTube Video
⏱  Duration: 12:34
👁  Views  : 1,234,567

Select quality:
  1) Best available (default)
  2) 1080p
  3) 720p
  4) 480p
  5) Audio only (MP3)

Enter choice [1-5] (press Enter for best): 1
Save to folder [press Enter for 'downloads']: 

⬇  Downloading (best) …
  100%  — processing file …          
✅ Saved to: /path/to/youtube_video_downloader/downloads
```

---

### Option 2: Advanced Resolution Inspector (`yt_downloader_2.0.py`)

Fetches all available resolutions, FPS, and file size estimates, then lets you pick the exact stream:

```bash
python3 yt_downloader_2.0.py
```

Example session:
```text
====================================================
   YouTube Downloader  —  all resolutions
====================================================
🔧 JS runtime : node

Available resolutions:
  #    Resolution   FPS    Ext    Size        
  ------------------------------------------
  1    2160p        60fps  mp4    3.2 GB      
  2    1440p        60fps  mp4    1.8 GB      
  3    1080p        60fps  mp4    950 MB      
  4    720p         60fps  mp4    420 MB      
  5    480p         30fps  mp4    180 MB      
  6    Audio only   —      mp3    —           

Pick a number [1-6]: 1
Save folder [Enter = 'downloads']: 
```

---

## 📁 Project Structure

```text
youtube_video_downloader/
├── downloads/             # Default destination for downloaded files
│   └── .gitkeep
├── yt_downloader.py       # Standard preset-based downloader
├── yt_downloader_2.0.py   # Advanced resolution-picker downloader
├── requirements.txt       # Python dependencies
├── .gitignore             # Ignores large media files and caches
└── README.md              # Project documentation
```

---

## 🛠 Troubleshooting

- **HTTP Error 403: Forbidden**: Ensure you have Node.js or Deno installed on your system (`which node`). The script uses Node to solve YouTube's dynamic JavaScript signature challenges.
- **Outdated yt-dlp**: YouTube regularly updates its streaming backend. If downloads fail, update `yt-dlp`:
  ```bash
  pip install --upgrade yt-dlp
  ```
