; Inno Setup script for Facebook Live Collector Pro.
; Compile with ISCC.exe (Inno Setup Compiler) after running scripts/build_exe.py.
; PrivilegesRequired=lowest because the app writes to %LOCALAPPDATA%, not Program Files -
; avoids an unnecessary admin-elevation prompt.

[Setup]
AppId={{B6C3D9E1-2F4A-4E7B-9C1D-FBLIVECOLLECTOR}}
AppName=Facebook Live Collector Pro
AppVersion=1.0.0
AppPublisher=Facebook Live Collector Pro
DefaultDirName={autopf}\FBLiveCollectorPro
DefaultGroupName=FB Live Collector Pro
OutputDir=..\dist\installer
OutputBaseFilename=FBLiveCollectorPro-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icons\app.ico
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\FBLiveCollectorPro.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "..\dist\FBLiveCollectorPro.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\FB Live Collector Pro"; Filename: "{app}\FBLiveCollectorPro.exe"
Name: "{autodesktop}\FB Live Collector Pro"; Filename: "{app}\FBLiveCollectorPro.exe"; Tasks: desktopicon
Name: "{group}\Uninstall FB Live Collector Pro"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\FBLiveCollectorPro.exe"; Description: "Launch FB Live Collector Pro"; Flags: nowait postinstall skipifsilent
