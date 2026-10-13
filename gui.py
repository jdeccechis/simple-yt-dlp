"""Simple yt-dlp GUI. No yt-dlp imports or network calls during startup."""
import json
import os
import queue
import signal
import subprocess
import threading
import tkinter as tk
from collections import deque
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from core import (SOURCES, RESOLUTIONS, FORMATS, PROGRESS_PREFIX, FILE_PREFIX,
                  POST_PREFIX, default_downloads, load_settings, save_settings,
                  validate_url, build_command, runtime_env, find_tool)


class App:
    def __init__(self, root):
        self.root = root
        self.process = None
        self.lock = threading.Lock()
        self.cancel_event = threading.Event()
        self.events = queue.Queue()
        self.busy = False
        self.indeterminate = False
        self.files = []
        self.log = deque(maxlen=150)
        saved = load_settings()
        self.source = tk.StringVar(value=saved.get('source') if saved.get('source') in SOURCES else 'YouTube')
        self.url = tk.StringVar()
        self.folder = tk.StringVar(value=str(saved.get('folder') or default_downloads()))
        self.format = tk.StringVar(value='MP4')
        self.resolution = tk.StringVar(value='Best available')
        self.status = tk.StringVar(value='Paste a video link to get started.')
        self.expanded = False
        root.title('Simple yt-dlp')
        root.geometry('620x420')
        root.minsize(540, 420)
        style = ttk.Style()
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TButton', padding=(10, 5))
        outer = ttk.Frame(root, padding=20)
        outer.pack(fill='both', expand=True)
        outer.columnconfigure(1, weight=1)
        ttk.Label(outer, text='Simple yt-dlp', style='Title.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 16))
        ttk.Label(outer, text='Select source').grid(row=1, column=0, sticky='w', padx=(0, 12))
        self.source_box = ttk.Combobox(outer, textvariable=self.source, values=tuple(SOURCES), state='readonly', width=19)
        self.source_box.grid(row=1, column=1, sticky='w')
        ttk.Label(outer, text='Video URL').grid(row=2, column=0, sticky='w', pady=12)
        self.url_entry = ttk.Entry(outer, textvariable=self.url)
        self.url_entry.grid(row=2, column=1, columnspan=2, sticky='ew', pady=12)
        ttk.Label(outer, text='Save to').grid(row=3, column=0, sticky='w')
        self.folder_entry = ttk.Entry(outer, textvariable=self.folder)
        self.folder_entry.grid(row=3, column=1, sticky='ew')
        self.browse_btn = ttk.Button(outer, text='Browse…', command=self.browse)
        self.browse_btn.grid(row=3, column=2, padx=(8, 0))
        self.advance_btn = ttk.Button(outer, text='+ Advanced', command=self.toggle)
        self.advance_btn.grid(row=4, column=0, columnspan=3, sticky='w', pady=(12, 0))
        self.advanced = ttk.Frame(outer, padding=(0, 10, 0, 0))
        self.advanced.columnconfigure(1, weight=1)
        ttk.Label(self.advanced, text='Format').grid(row=0, column=0, sticky='w', padx=(0, 16))
        self.format_box = ttk.Combobox(self.advanced, textvariable=self.format, values=FORMATS, state='readonly', width=12)
        self.format_box.grid(row=0, column=1, sticky='w')
        ttk.Label(self.advanced, text='Resolution').grid(row=1, column=0, sticky='w', pady=(8, 0), padx=(0, 16))
        self.resolution_box = ttk.Combobox(self.advanced, textvariable=self.resolution, values=RESOLUTIONS, state='readonly', width=20)
        self.resolution_box.grid(row=1, column=1, sticky='w', pady=(8, 0))
        ttk.Label(self.advanced, text='Maximum height; original dimensions are preserved.', foreground='#555555').grid(row=2, column=0, columnspan=2, sticky='w', pady=(8, 0))
        actions = ttk.Frame(outer)
        actions.grid(row=6, column=0, columnspan=3, sticky='ew', pady=(16, 8))
        self.download_btn = ttk.Button(actions, text='Download', command=self.download)
        self.download_btn.pack(side='left')
        self.cancel_btn = ttk.Button(actions, text='Cancel', command=self.cancel, state='disabled')
        self.cancel_btn.pack(side='left', padx=8)
        ttk.Button(actions, text='Details', command=self.details).pack(side='right')
        self.progress = ttk.Progressbar(outer, maximum=100)
        self.progress.grid(row=7, column=0, columnspan=3, sticky='ew')
        ttk.Label(outer, textvariable=self.status, wraplength=560).grid(row=8, column=0, columnspan=3, sticky='w', pady=(8, 0))
        self.url_entry.focus_set()
        root.bind('<Return>', lambda event: self.download() if not self.busy else None)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after_idle(self.fit_window)
        root.after(100, self.poll)

    def browse(self):
        folder = filedialog.askdirectory(initialdir=self.folder.get(), title='Choose download folder')
        if folder:
            self.folder.set(folder)
            self.remember()

    def remember(self):
        try:
            save_settings({'source': self.source.get(), 'folder': self.folder.get()})
        except OSError as exc:
            self.log.append('Could not save preferences: ' + str(exc))

    def toggle(self):
        self.expanded = not self.expanded
        if self.expanded:
            self.advanced.grid(row=5, column=0, columnspan=3, sticky='ew')
        else:
            self.advanced.grid_remove()
        self.advance_btn.configure(text='− Advanced' if self.expanded else '+ Advanced')
        self.fit_window()

    def fit_window(self):
        self.root.update_idletasks()
        height = max(420, self.root.winfo_reqheight() + 4)
        self.root.geometry(f'{max(620, self.root.winfo_width())}x{height}')

    def set_busy(self, busy):
        self.busy = busy
        for widget in (self.url_entry, self.folder_entry, self.browse_btn, self.download_btn):
            widget.configure(state='disabled' if busy else 'normal')
        for widget in (self.source_box, self.format_box, self.resolution_box):
            widget.configure(state='disabled' if busy else 'readonly')
        self.cancel_btn.configure(state='normal' if busy else 'disabled')

    def activity(self, active):
        if active != self.indeterminate:
            self.progress.stop()
            self.progress.configure(mode='indeterminate' if active else 'determinate')
            self.indeterminate = active
            if active:
                self.progress.start(12)

    def download(self):
        if self.busy:
            return
        try:
            url = validate_url(self.source.get(), self.url.get())
            if not self.folder.get().strip():
                raise ValueError('Choose a download folder first.')
            folder = Path(self.folder.get()).expanduser().resolve()
            folder.mkdir(parents=True, exist_ok=True)
            env = runtime_env()
            ffmpeg = find_tool('ffmpeg', env)
            if not ffmpeg or not find_tool('ffprobe', env):
                raise ValueError('FFmpeg / FFprobe was not found. Run Setup.cmd, or put both executables in the tools folder.')
            if self.source.get() == 'YouTube' and not find_tool('deno', env):
                raise ValueError('Deno was not found. Run Setup.cmd for full YouTube support, or put deno.exe in tools.')
            cmd = build_command(url, folder, self.format.get(), self.resolution.get(), ffmpeg)
        except (ValueError, OSError) as exc:
            messagebox.showerror('Cannot start download', str(exc))
            return
        self.remember()
        self.files.clear()
        self.log.clear()
        self.cancel_event.clear()
        self.progress['value'] = 0
        self.status.set('Connecting and finding the best available video…')
        self.set_busy(True)
        self.activity(True)
        threading.Thread(target=self.run, args=(cmd, env), daemon=True).start()

    def run(self, cmd, env):
        try:
            kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
            with self.lock:
                if self.cancel_event.is_set():
                    self.events.put(('done', -1))
                    return
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           text=True, encoding='utf-8', errors='replace', env=env, **kwargs)
                self.process = process
            with process.stdout:
                for line in process.stdout:
                    self.events.put(('line', line.rstrip()))
            code = process.wait()
            with self.lock:
                self.process = None
            self.events.put(('done', code))
        except Exception as exc:
            with self.lock:
                self.process = None
            self.events.put(('line', 'ERROR: ' + str(exc)))
            self.events.put(('done', 1))

    def cancel(self):
        self.cancel_event.set()
        self.cancel_btn.configure(state='disabled')
        self.status.set('Cancelling…')
        threading.Thread(target=self.kill_process, daemon=True).start()

    def kill_process(self):
        with self.lock:
            process = self.process
            if process is None or process.poll() is not None:
                return
            try:
                if os.name == 'nt':
                    # Kill yt-dlp AND its FFmpeg/Deno subprocesses.
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, check=True)
                else:
                    os.killpg(process.pid, signal.SIGTERM)
            except (OSError, subprocess.SubprocessError):
                process.kill()

    def handle_line(self, line):
        if line.startswith(PROGRESS_PREFIX):
            try:
                data = json.loads(line[len(PROGRESS_PREFIX):])
                if data.get('status') == 'downloading':
                    total = data.get('total_bytes') or data.get('total_bytes_estimate')
                    downloaded = data.get('downloaded_bytes') or 0
                    self.activity(not bool(total))
                    if total:
                        percent = min(100, downloaded / total * 100)
                        self.progress['value'] = percent
                        text = f'Downloading: {percent:.1f}%'
                    else:
                        text = f'Downloading: {downloaded / 1048576:.1f} MB'
                    if data.get('speed'):
                        text += f"  •  {data['speed'] / 1048576:.1f} MB/s"
                    if data.get('eta') is not None:
                        text += f"  •  {int(data['eta'])}s remaining"
                    self.status.set(text)
                elif data.get('status') == 'finished':
                    self.activity(True)
                    self.status.set('Stream downloaded. Merging / converting if needed…')
            except (ValueError, TypeError, AttributeError):
                self.log.append(line)
        elif line.startswith(FILE_PREFIX):
            try:
                self.files.append(json.loads(line[len(FILE_PREFIX):]))
            except ValueError:
                self.log.append(line)
        elif line.startswith(POST_PREFIX):
            self.activity(True)
            self.status.set('Merging / converting… This can take longer than the download.')
        else:
            self.log.append(line)

    def poll(self):
        # Limit each pass so long logs cannot block UI input.
        for _ in range(200):
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'line':
                self.handle_line(value)
            else:
                self.activity(False)
                self.set_busy(False)
                if self.cancel_event.is_set():
                    self.progress['value'] = 0
                    self.status.set('Cancelled. Partial files may remain; retry to resume.')
                elif value == 0 and self.files:
                    self.progress['value'] = 100
                    self.status.set('Saved: ' + Path(self.files[-1]).name)
                    self.log.extend('Saved: ' + p for p in self.files)
                else:
                    self.progress['value'] = 0
                    self.status.set('Download failed. Open Details for the error.')
                    error = next((s for s in reversed(self.log) if 'ERROR:' in s), 'No completed video was returned.')
                    messagebox.showerror('Download failed', error + '\n\nUse Details for the full log. If yt-dlp is missing, run Setup.cmd.')
        self.root.after(100, self.poll)

    def details(self):
        window = tk.Toplevel(self.root)
        window.title('Download details')
        window.geometry('700x340')
        box = tk.Text(window, wrap='word', padx=10, pady=10)
        scroll = ttk.Scrollbar(window, command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        box.pack(fill='both', expand=True)
        box.insert('1.0', '\n'.join(self.log) or 'No download log yet.')
        box.configure(state='disabled')

    def close(self):
        if self.busy:
            if not messagebox.askyesno('Close', 'Cancel the current download and close?'):
                return
            self.cancel_event.set()
            self.status.set('Cancelling before closing…')
            threading.Thread(target=self.kill_process, daemon=True).start()
            self.wait_to_close()
        else:
            self.remember()
            self.root.destroy()

    def wait_to_close(self):
        if self.busy:
            self.root.after(100, self.wait_to_close)
        else:
            self.remember()
            self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
