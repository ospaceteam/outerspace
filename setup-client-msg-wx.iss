[Setup]
AppName=Outer Space Message Center
AppVerName=Outer Space Message Center 0.1
AppPublisher=Anderuso
AppVersion=0.1
AppPublisherURL=http://www.ospace.net
AppSupportURL=http://www.ospace.net
AppUpdatesURL=http://www.ospace.net
DefaultDirName={pf}\Outer Space Message Center
DefaultGroupName=Outer Space Message Center
AllowNoIcons=yes
ExtraDiskSpaceRequired=5242880
DisableStartupPrompt=yes
OutputBaseFilename=OuterSpaceMessageCenter
OutputDir=server\website\osclient
InfoBeforeFile=license.rtf
SolidCompression=no
Compression=bzip

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; MinVersion: 4,4
Name: "quicklaunchicon"; Description: "Create a &Quick Launch icon"; GroupDescription: "Additional icons:"; MinVersion: 4,4; Flags: unchecked

[Dirs]
Name: "{app}\var"; Flags: deleteafterinstall

[Files]
Source: "client-msg-wx\dist32\*"; DestDir: "{app}"; CopyMode: alwaysoverwrite; Flags: recursesubdirs

[INI]
Filename: "{app}\osc.url"; Section: "InternetShortcut"; Key: "URL"; String: "http://www.ospace.net/"

[Icons]
Name: "{group}\Outer Space Message Center"; Filename: "{app}\oscmsg.exe"; WorkingDir: "{app}"; IconFilename: "{app}\res\bigicon.ico"
Name: "{group}\IGE Website"; Filename: "{app}\osc.url"
Name: "{group}\README_CZ.TXT"; Filename: "{app}\README_CZ.TXT"
Name: "{group}\README_EN.TXT"; Filename: "{app}\README_EN.TXT"
Name: "{userdesktop}\Outer Space Message Center"; Filename: "{app}\oscmsg.exe"; MinVersion: 4,4; Tasks: desktopicon; IconFilename: "{app}\res\bigicon.ico"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Outer Space Message Center"; Filename: "{app}\osc.exe"; MinVersion: 4,4; Tasks: quicklaunchicon; IconFilename: "{app}\res\bigicon.ico"

[Run]
Filename: "{app}\oscmsg.exe"; Description: "Launch Outer Space Message Center"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\osc.url"
