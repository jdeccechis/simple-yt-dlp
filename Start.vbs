Option Explicit
Dim shell, fso, folder, python, app
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
python = folder & "\.venv\Scripts\pythonw.exe"
app = folder & "\app.pyw"
If Not fso.FileExists(python) Then
    MsgBox "Please run Setup.cmd once before starting Simple yt-dlp.", 48, "Simple yt-dlp"
    WScript.Quit 1
End If
shell.CurrentDirectory = folder
shell.Run Chr(34) & python & Chr(34) & " " & Chr(34) & app & Chr(34), 0, False
