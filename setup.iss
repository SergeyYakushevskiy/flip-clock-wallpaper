[Setup]
AppName=FlipClock Live Wallpaper
AppVersion=1.0
DefaultDirName={autopf}\FlipClockWallpaper
DefaultGroupName=Digital Live Wallpaper
UninstallDisplayIcon={app}\app.exe
Compression=lzma2
SolidCompression=yes
OutputDir=setup_output
OutputBaseFilename=LiveWallpaper_Installer
SetupIconFile=assets\app_icon.ico

PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline dialog

[Dirs]
Name: "{userappdata}\DigitalWallpaper"; Permissions: users-full

[Files]
; Основной exe после сборки PyInstaller
Source: "dist\app.exe"; DestDir: "{app}"; Flags: ignoreversion
; Иконка приложения
Source: "assets\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Конфиг
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
; Шрифт
Source: "assets\digital-7.ttf"; DestDir: "{autofonts}"; FontInstall: "Digital-7"; Flags: onlyifdestfileexists uninsneveruninstall

[Icons]
Name: "{group}\Digital Live Wallpaper"; Filename: "{app}\app.exe"
; Автозагрузка для текущего пользователя
Name: "{userstartup}\Digital Live Wallpaper"; Filename: "{app}\app.exe"; WorkingDir: "{userappdata}\DigitalWallpaper"
; Ярлык для папки настроек
Name: "{group}\Открыть папку настроек"; Filename: "explorer.exe"; Parameters: "{userappdata}\DigitalWallpaper"

[Run]
Filename: "{app}\app.exe"; Description: "Запустить обои сейчас"; Flags: nowait postinstall skipifsilent
