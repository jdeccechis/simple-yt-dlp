"""Lightweight configuration and yt-dlp command construction (standard library only)."""
import json
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
SOURCES = {
    'YouTube': ('youtube.com', 'youtu.be', 'youtube-nocookie.com'),
    'Instagram': ('instagram.com',),
    'Twitter / X': ('twitter.com', 'x.com', 't.co'),
    'Bilibili': ('bilibili.com', 'b23.tv', 'bilibili.tv'),
}
RESOLUTIONS = ('Best available', '2160p (4K)', '1440p', '1080p', '720p',
               '480p', '360p', '240p', '144p')
FORMATS = ('MP4', 'MKV', 'WebM', 'AVI')
PROGRESS_PREFIX = '__GUI_PROGRESS__'
FILE_PREFIX = '__GUI_FILE__'
POST_PREFIX = '__GUI_POST__'


def default_downloads():
    # Respect Windows' redirected Downloads known folder (including OneDrive).
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
                value = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
                return Path(os.path.expandvars(value))
        except OSError:
            pass
    return Path.home() / 'Downloads'


def settings_path():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.config'))) / 'SimpleYtDlp' / 'settings.json'


def load_settings():
    try:
        data = json.loads(settings_path().read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(data):
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def validate_url(source, value):
    value = value.strip()
    try:
        parts = urlsplit(value)
        host = (parts.hostname or '').lower()
        if parts.scheme not in ('https', 'http') or not host or parts.username or parts.password:
            raise ValueError('Paste a complete http:// or https:// video URL.')
        if source not in SOURCES or not any(host == d or host.endswith('.' + d) for d in SOURCES[source]):
            raise ValueError('The URL does not match the selected source.')
        if any(c.isspace() for c in value):
            raise ValueError('The URL must not contain spaces or line breaks.')
    except (ValueError, TypeError) as exc:
        raise ValueError(str(exc)) from exc
    return value


def runtime_env():
    env = os.environ.copy()
    paths = [str(ROOT / 'tools')]
    if os.name == 'nt':
        paths += [str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'WinGet' / 'Links')]
        # Explorer can retain the old PATH after winget installs a dependency.
        try:
            import winreg
            for hive, key in ((winreg.HKEY_CURRENT_USER, 'Environment'),
                    (winreg.HKEY_LOCAL_MACHINE,
                     r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')):
                with winreg.OpenKey(hive, key) as handle:
                    paths.append(os.path.expandvars(winreg.QueryValueEx(handle, 'Path')[0]))
        except OSError:
            pass
    paths.append(env.get('PATH', ''))
    env['PATH'] = os.pathsep.join(paths)
    env['PYTHONUTF8'] = '1'
    env['PYTHONUNBUFFERED'] = '1'
    return env


def backend_python():
    candidate = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if candidate.is_file():
        return str(candidate)
    current = Path(sys.executable)
    if current.name.lower() == 'pythonw.exe':
        current = current.with_name('python.exe')
    return str(current)


def build_command(url, folder, file_format, resolution, ffmpeg=None):
    if file_format not in FORMATS or resolution not in RESOLUTIONS:
        raise ValueError('Choose a supported format and resolution.')
    cap = None if resolution == RESOLUTIONS[0] else int(resolution.split('p')[0])
    filter_ = '' if cap is None else f'[height<={cap}]'
    selector = f'bv*{filter_}+ba/b{filter_}/bv*{filter_}'
    cmd = [backend_python(), '-u', '-m', 'yt_dlp',
           '--ignore-config', '--no-plugin-dirs', '--no-playlist',
           '--no-simulate', '--no-colors', '--newline', '--progress',
           '--progress-delta', '0.2', '--encoding', 'utf-8',
           '--progress-template', f'download:{PROGRESS_PREFIX}%(progress)j',
           '--progress-template', f'postprocess:{POST_PREFIX}%(progress.status)s',
           '--print', f'after_move:{FILE_PREFIX}%(filepath)j',
           '--format', selector, '--format-sort', 'res,fps,br', '--format-sort-force',
           '--merge-output-format', 'mkv', '--windows-filenames',
           '--no-overwrites', '--no-post-overwrites', '--paths', str(folder),
           '--output', '%(title).150B [%(id)s].%(ext)s']
    target = file_format.lower()
    if target == 'mkv':
        cmd += ['--remux-video', target]
    else:
        codecs = {
            'mp4': '-c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k -movflags +faststart',
            'webm': '-c:v libvpx-vp9 -crf 24 -b:v 0 -c:a libopus -b:a 160k',
            'avi': '-c:v mpeg4 -q:v 3 -c:a libmp3lame -b:a 192k',
        }
        cmd += ['--recode-video', target, '--postprocessor-args',
                'VideoConvertor+ffmpeg_o:' + codecs[target]]
    if ffmpeg:
        cmd += ['--ffmpeg-location', ffmpeg]
    cmd += ['--', url]
    return cmd


def find_tool(name, env=None):
    return shutil.which(name, path=(env or runtime_env()).get('PATH'))
