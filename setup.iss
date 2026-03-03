[Setup]
AppName=Digital Live Wallpaper
AppVersion=1.0
DefaultDirName={autopf}\DigitalWallpaper
DefaultGroupName=Digital Live Wallpaper
UninstallDisplayIcon={app}\wallpaper.exe
Compression=lzma2
SolidCompression=yes
OutputDir=setup_output
OutputBaseFilename=LiveWallpaper_Installer
SetupIconFile=app_icon.ico

PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline dialog

[Dirs]
Name: "{userappdata}\DigitalWallpaper"; Permissions: users-full

[Files]
Source: "dist\wallpaper.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion

Source: "digital-7.ttf"; DestDir: "{autofonts}"; FontInstall: "Digital-7"; Flags: onlyifdestfileexists uninsneveruninstall

[Icons]
Name: "{group}\Digital Live Wallpaper"; Filename: "{app}\wallpaper.exe"
; Автозагрузка для текущего пользователя
Name: "{userstartup}\Digital Live Wallpaper"; Filename: "{app}\wallpaper.exe"; WorkingDir: "{userappdata}\DigitalWallpaper"
; Ярлык для настроек (откроет папку, которую создаст Python)
Name: "{group}\Открыть папку настроек"; Filename: "explorer.exe"; Parameters: "{userappdata}\DigitalWallpaper"

[Run]
Filename: "{app}\wallpaper.exe"; Description: "Запустить обои сейчас"; Flags: nowait postinstall skipifsilent