[Setup]
AppName=Convertisor
AppVersion=1.0.0
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
Source: "dist\Convertisor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Convertisor"; Filename: "{app}\Convertisor.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\Convertisor"; Filename: "{app}\Convertisor.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Convertisor.exe"; Description: "Lancer Convertisor"; Flags: nowait postinstall skipifsilent