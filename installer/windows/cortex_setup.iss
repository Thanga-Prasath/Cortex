; Cortex Voice Assistant — Inno Setup Script
; Requires: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Usage:  Open this file in Inno Setup Compiler → Build → Compile

[Setup]
AppName=Cortex
AppVersion=1.0.0
AppPublisher=Cortex Project
AppPublisherURL=https://github.com/Thanga-Prasath/Cortex
DefaultDirName={autopf}\Cortex
DefaultGroupName=Cortex
OutputDir=..\..\dist\installer
OutputBaseFilename=setup
SetupIconFile=..\..\icon.ico
UninstallDisplayIcon={app}\Cortex.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start Cortex automatically when Windows starts"; GroupDescription: "Startup:"; Flags: checked

[Files]
; Bundle the entire PyInstaller output directory
Source: "..\..\dist\Cortex\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Cortex"; Filename: "{app}\Cortex.exe"; IconFilename: "{app}\Cortex.exe"
Name: "{group}\Uninstall Cortex"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Cortex"; Filename: "{app}\Cortex.exe"; Tasks: desktopicon; IconFilename: "{app}\Cortex.exe"

[Registry]
; Auto-startup: Add to Windows Run registry key (only if user selected the autostart task)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Cortex"; ValueData: """{app}\Cortex.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\Cortex.exe"; Description: "Launch Cortex"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Clean up any auto-start entries on uninstall (handled by uninsdeletevalue flag above)

[UninstallDelete]
Type: files; Name: "{app}\temp_cmd.bat"
