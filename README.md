[Download the latest version](https://github.com/YOUR_USERNAME/simple-yt-dlp-gui/releases/latest/download/yt-dlp-gui.zip)

SIMPLE YT-DLP - Windows 11 / Python 3.10+

QUICK START
1. Extract this entire ZIP to a folder you can write to. Do not run inside the ZIP.
2. Double-click Setup.cmd once. It creates a private Python environment and
   installs yt-dlp. If FFmpeg or Deno is missing, it offers to install them using
   Windows winget. These downloads require internet and can take a few minutes.
3. Double-click Start.vbs to open the GUI without a terminal window.
   If Windows disables VBScript, use Start.cmd instead (brief terminal flash).
4. Select the source, paste a video URL, and choose a folder with Browse.
   Downloads is the initial destination; your last chosen folder is remembered.
5. Click Download. Use Cancel to stop, or Details to view an error.

ADVANCED (+)
Format: MP4 (default), MKV, WebM, AVI.
Resolution: Best available (default), 2160p/4K, 1440p, 1080p, 720p,
            480p, 360p, 240p, 144p.

Best available prioritizes the highest available source resolution and includes
sound when the source supplies it. Nothing is upscaled or stretched: a source
that is 600 x 600 stays 600 x 600. Resolution choices are maximum HEIGHT limits
in pixels, including for portrait videos. They select an existing source stream;
they do not resize it. If no stream at/below the limit exists, the download fails
with an explanation rather than silently downloading a larger stream.

MKV preserves the original video/audio through remuxing. MP4, WebM and AVI convert
when the downloaded container differs from the selected format. This preserves
dimensions but re-encoding can take time and slightly change quality. WebM
conversion in particular can be slow. Use MKV to avoid re-encoding. A file already
in the selected format is retained without re-encoding. MP4 does not guarantee
H.264 if the original source is already MP4.

The progress bar tracks the current video/audio stream, so it can restart when
the second stream begins. An animated bar means extraction/merging/conversion.
Downloads run in the background so the interface stays responsive.
YouTube playlist URLs containing a single video download that video only.
This first version is intended for individual videos/posts, not playlist batches.
Multi-video social posts may produce multiple files. Photos are not downloaded.
Existing download files are not deliberately overwritten. Cancellation may leave
partial files; retrying the same URL/destination can resume the download.

UPDATES / TROUBLESHOOTING
- Rerun Setup.cmd to update yt-dlp when a website changes or downloads fail.
- If Python is not found, install Python 3.10+ from python.org with Tcl/Tk support.
  Enable "Add Python to PATH" in the installer, or install the Python launcher.
- If winget is missing, install/update "App Installer" from the Microsoft Store.
- Manual tool installation is also supported: put ffmpeg.exe, ffprobe.exe and
  deno.exe directly in the included tools folder, then rerun Setup.cmd.
- A site may require sign-in, impose geographic restrictions, or limit available
  quality. This version does not import cookies or implement login. If a video
  requires authentication, the Details log explains the failure. Bilibili's
  anonymously available maximum can be lower than the logged-in maximum.
- Opening the window involves no network checks or yt-dlp imports. Startup aims
  to stay under three seconds, but depends on your PC and antivirus. This package
  has been checked in a Linux environment, not benchmarked on Windows 11.
- Start.cmd and app.pyw are alternatives if Start.vbs is blocked.
- Keep all files together. If you move the folder to another location or PC,
  delete .venv and rerun Setup.cmd; Python virtual environments are not relocatable.
  Python and any system-installed tools must be available on the destination PC.
- Preferences live in %LOCALAPPDATA%\SimpleYtDlp\settings.json.

WHAT IS INCLUDED
Python source, double-click launch/setup scripts, and this README.
No precompiled Windows .exe or third-party binaries are included. Your installed
Python runs the GUI. Setup installs the download engine separately from the GUI.

PROJECT LINKS / DEPENDENCIES
https://github.com/yt-dlp/yt-dlp
https://github.com/yt-dlp/FFmpeg-Builds/releases
https://deno.com/
https://www.python.org/downloads/windows/
Dependencies retain their own licenses. No login credentials are collected.
