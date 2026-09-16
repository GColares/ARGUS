Set fso = CreateObject("Scripting.FileSystemObject")
currentPath = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = currentPath
WshShell.Run chr(34) & currentPath & "\iniciar.bat" & Chr(34), 0
Set WshShell = Nothing