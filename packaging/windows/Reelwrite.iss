; Inno Setup script for Reelwrite
; Build after PyInstaller: packaging/windows/build.ps1

#define MyAppName "Reelwrite"
#ifndef MyAppVersion
#define MyAppVersion "0.1.0"
#endif
#define MyAppPublisher "Somerville EdTec"
; Reelwrite.exe is the Tauri shell (src-tauri/target/release/Reelwrite.exe), copied
; into the bundle by build.ps1. It falls back to the PyInstaller browser launcher when
; the Tauri build is skipped, so the filename stays the same either way.
; Tauri needs the WebView2 runtime: evergreen on Windows 10 21H2+/11. To support older
; images, add the Microsoft bootstrapper to [Files] and run it from [Run] before launch.
#define MyAppExeName "Reelwrite.exe"
#define DistDir "..\..\dist\windows"

[Setup]
AppId={{A7C3E8F1-9B2D-4E6A-8F01-2C4D6E8A0B12}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Reelwrite
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#DistDir}\installer
OutputBaseFilename=ReelwriteSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
AppMutex=ReelwriteSingleInstance

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistDir}\bundle\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop running Reelwrite / API / vendored ffmpeg before files are removed.
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\uninstall_kill.ps1"" -InstallDir ""{app}"""; Flags: runhidden; RunOnceId: "KillReelwrite"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\vendor\models\*"
; Keep user projects under {localappdata}\Reelwrite\projects
