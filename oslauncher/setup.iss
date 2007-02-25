[Setup]
AppName=Outer Space Launcher
AppVerName=Outer Space Launcher 0.2.1
AppPublisher=Ludek Smid
AppVersion=0.2.1
AppPublisherURL=http://www.ospace.net
AppSupportURL=http://www.ospace.net
AppUpdatesURL=http://www.ospace.net
DefaultDirName={pf}\Outer Space
DefaultGroupName=Outer Space
AllowNoIcons=yes
ExtraDiskSpaceRequired=5242880
DisableStartupPrompt=yes
OutputBaseFilename=OuterSpaceLauncher-0.2.1
OutputDir=.
InfoBeforeFile=license.rtf
SolidCompression=no
Compression=bzip

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; MinVersion: 4,4
Name: "quicklaunchicon"; Description: "Create a &Quick Launch icon"; GroupDescription: "Additional icons:"; MinVersion: 4,4; Flags: unchecked

[Dirs]
Name: "{app}\var"; Flags: deleteafterinstall

[Files]
Source: "dist_win32\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[INI]
Filename: "{app}\outerspace.url"; Section: "InternetShortcut"; Key: "URL"; String: "http://www.ospace.net/"

[Icons]
Name: "{group}\Outer Space"; Filename: "{app}\outerspace.exe"; WorkingDir: "{app}"; IconFilename: "{app}\oslauncher\res\bigicon.ico"
Name: "{group}\Outer Space Web"; Filename: "{app}\outerspace.url"
Name: "{group}\README"; Filename: "notepad.exe"; Parameters: "{app}\README"
Name: "{group}\ChangeLog"; Filename: "notepad.exe"; Parameters: "{app}\ChangeLog"
Name: "{group}\Uninstall Outer Space"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Outer Space"; Filename: "{app}\outerspace.exe"; MinVersion: 4,4; Tasks: desktopicon; IconFilename: "{app}\oslauncher\res\bigicon.ico"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Outer Space"; Filename: "{app}\outerspace.exe"; MinVersion: 4,4; Tasks: quicklaunchicon; IconFilename: "{app}\oslauncher\res\bigicon.ico"

[Run]
Filename: "{app}\outerspace.exe"; Description: "Launch Outer Space"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\outerspace.url"
