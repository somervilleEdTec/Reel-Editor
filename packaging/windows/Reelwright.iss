; Inno Setup script for Reelwright
; Build after PyInstaller: packaging/windows/build.ps1

#define MyAppName "Reelwright"
#ifndef MyAppVersion
#define MyAppVersion "0.1.0"
#endif
#define MyAppPublisher "Somerville EdTec"
#define MyAppExeName "Reelwright.exe"
#define DistDir "..\..\dist\windows"

[Setup]
AppId={{A7C3E8F1-9B2D-4E6A-8F01-2C4D6E8A0B12}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Reelwright
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#DistDir}\installer
OutputBaseFilename=ReelwrightSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
AppMutex=ReelwrightSingleInstance

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
; Stop running Reelwright / API / vendored ffmpeg before files are removed.
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\uninstall_kill.ps1"" -InstallDir ""{app}"""; Flags: runhidden; RunOnceId: "KillReelwright"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\vendor\models\*"
; Keep user projects under {localappdata}\Reelwright\projects
