; Inno Setup 脚本：EXG 僵尸逃跑自动加入安装包
#define MyAppName "EXG 僵尸逃跑自动加入"
#define MyAppVersion "1.0.0"
#define MyAppExeName "EXG-AutoJoin.exe"
#define MyAppPublisher "cht100"
#define MyAppURL "https://github.com/cht100/exg-auto-join"

[Setup]
AppId={{8F3B2C4A-6D4E-4A2B-9C1E-2F0A5D7E8B91}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\EXG-AutoJoin
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=EXG-AutoJoin-Setup
SetupIconFile=assets\darkrp.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "立即运行 {#MyAppName}"; Flags: nowait postinstall skipifsilent
