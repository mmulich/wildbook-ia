; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!
; http://www.jrsoftware.org/isdl.php
; http://www.jrsoftware.org/download.php/is-unicode.exe?site=1

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={47BE3DA2-261D-4672-9849-18BB2EB382FC}
AppName=IBEIS
AppVersion=1
;AppVerName=IBEIS 1
AppPublisher=Rensselaer Polytechnic Institute
AppPublisherURL=www.rpi.edu/~crallj/
AppSupportURL=www.rpi.edu/~crallj/
AppUpdatesURL=www.rpi.edu/~crallj/
DefaultDirName={pf}\IBEIS
DefaultGroupName=IBEIS
OutputBaseFilename=ibeis-win32-setup
SetupIconFile=ibsicon.ico
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\ibeis\IBEISApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\ibeis\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\ibeis"; Filename: "{app}\IBEISApp.exe"
Name: "{commondesktop}\ibeis"; Filename: "{app}\IBEISApp.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\IBEISApp.exe"; Description: "{cm:LaunchProgram,IBEIS}"; Flags: nowait postinstall skipifsilent
