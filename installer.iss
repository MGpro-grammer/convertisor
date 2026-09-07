; Lecture de la version depuis version.txt : source unique de verite,
; partagee avec l'application (voir core/config.py -> VERSION_FILE).
#define VersionFile FileOpen(AddBackslash(SourcePath) + "version.txt")
#define AppVer FileRead(VersionFile)
#expr FileClose(VersionFile)
#undef VersionFile

[Setup]
AppName=Convertisor
AppVersion={#AppVer}
AppPublisher=MGpro-grammer
DefaultDirName={autopf}\Convertisor
DefaultGroupName=Convertisor
OutputDir=installer
OutputBaseFilename=Convertisor-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\Convertisor.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le bureau"; GroupDescription: "Icônes supplémentaires"

[Files]
Source: "dist\Convertisor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Convertisor"; Filename: "{app}\Convertisor.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\Convertisor"; Filename: "{app}\Convertisor.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Convertisor.exe"; Description: "Lancer Convertisor"; Flags: postinstall skipifsilent shellexec