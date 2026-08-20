$ErrorActionPreference = "Stop"

$appDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $appDir "auto_join.pyw"
$icon = Join-Path $appDir "assets\darkrp.ico"
$python = (Get-Command python).Source
$pythonw = Join-Path (Split-Path -Parent $python) "pythonw.exe"
if (-not (Test-Path -LiteralPath $pythonw)) {
    $pythonw = $python
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutName = ([string]::Concat([char[]](0x50F5, 0x5C38, 0x9003, 0x8DD1, 0x81EA, 0x52A8, 0x52A0, 0x5165))) + ".lnk"
$shortcutPath = Join-Path $desktop $shortcutName

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = '"' + $launcher + '"'
$shortcut.WorkingDirectory = $appDir
$shortcut.Description = "EXG 僵尸逃跑服务器自动加入 / 空位监控"
if (Test-Path -LiteralPath $icon) {
    $shortcut.IconLocation = $icon
}
$shortcut.Save()

Write-Host "Created shortcut: $shortcutPath"
