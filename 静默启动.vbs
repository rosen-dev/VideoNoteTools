Set WshShell = CreateObject("WScript.Shell")
strPath = WScript.ScriptFullName
Set objFSO = CreateObject("Scripting.FileSystemObject")
strDir = objFSO.GetParentFolderName(strPath)

WshShell.CurrentDirectory = strDir

strLog = strDir & "\run_log.txt"
If objFSO.FileExists(strLog) Then
    Set objFile = objFSO.GetFile(strLog)
    If DateDiff("d", objFile.DateCreated, Now) >= 7 Then
        objFSO.DeleteFile strLog
    End If
End If

WshShell.Run "cmd.exe /c python main.py >> run_log.txt 2>&1", 0, False
