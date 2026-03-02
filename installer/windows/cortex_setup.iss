[Setup]
AppName=Cortex
AppVersion=1.0.0-beta
AppPublisher=Thanga-Prasath
AppPublisherURL=https://github.com/Thanga-Prasath/Cortex
AppSupportURL=https://github.com/Thanga-Prasath/Cortex/issues
AppUpdatesURL=https://github.com/Thanga-Prasath/Cortex/releases
DefaultDirName={autopf}\Cortex
DefaultGroupName=Cortex
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=Cortex-Setup-v1.0.0-beta-Windows
SetupIconFile=..\..\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\icon.ico
VersionInfoVersion=1.0.0.0
VersionInfoProductName=Cortex
VersionInfoDescription=Cortex Voice Assistant

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Application source files (NO piper_engine, NO whisper model — downloaded by launcher)
Source: "..\..\main.py";        DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\launcher.py";    DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\version.txt";    DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\icon.png";       DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\icon.ico";       DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\requirements-windows.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\setup.py";       DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\components\*";   DestDir: "{app}\components"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\core\*";         DestDir: "{app}\core"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\data\*";         DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "whisper_model\*"
Source: "..\..\scripts\*";      DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Cortex";               Filename: "{app}\launcher.py"; IconFilename: "{app}\icon.ico"; Comment: "Launch Cortex Voice Assistant"
Name: "{group}\Uninstall Cortex";     Filename: "{uninstallexe}"
Name: "{autodesktop}\Cortex";         Filename: "{app}\launcher.py"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\setup.py"; Parameters: ""; Description: "Run first-time setup"; Flags: postinstall shellexec skipifsilent
