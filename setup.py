"""One-time setup, or rerun to update yt-dlp."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    if sys.version_info < (3, 10):
        raise RuntimeError('Please install Python 3.10 or newer from https://www.python.org/downloads/windows/')
    import tkinter  # Fail clearly if the Python installer omitted Tcl/Tk.
    from core import find_tool, runtime_env
    print('Setting up Simple yt-dlp. Internet access is required.', flush=True)
    venv = ROOT / '.venv'
    if not (venv / 'Scripts' / 'python.exe').exists():
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
    python = str(venv / 'Scripts' / 'python.exe')
    subprocess.run([python, '-m', 'pip', 'install', '--upgrade', '-r', str(ROOT / 'requirements.txt')], check=True)
    for name, package in [('ffmpeg', 'Gyan.FFmpeg'), ('deno', 'DenoLand.Deno')]:
        if find_tool(name, runtime_env()):
            print(name + ' found.')
            continue
        print('\n' + name + ' is required. You can also put its executable in the tools folder.')
        if not find_tool('winget'):
            raise RuntimeError('Install Microsoft App Installer (winget), or install FFmpeg and Deno manually. See README.txt.')
        answer = input('Install ' + name + ' with Windows winget now? [Y/n] ').strip().lower()
        if answer not in ('', 'y', 'yes'):
            raise RuntimeError('Setup stopped. Install the missing tool manually, then rerun Setup.cmd.')
        subprocess.run(['winget', 'install', '--exact', '--id', package, '--source', 'winget',
                        '--accept-source-agreements', '--accept-package-agreements'], check=True)
    env = runtime_env()
    missing = [tool for tool in ('ffmpeg', 'ffprobe', 'deno') if not find_tool(tool, env)]
    if missing:
        raise RuntimeError('Not found: ' + ', '.join(missing) + '. Restart Windows and rerun Setup.cmd, or place the executables in tools.')
    subprocess.run([python, '-c', 'import tkinter, yt_dlp'], check=True)
    print('\nReady! Double-click Start.vbs (or Start.cmd) to open the GUI.')
    print('Rerun Setup.cmd whenever you want to update yt-dlp.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('\nSETUP ERROR: ' + str(exc))
        sys.exit(1)
