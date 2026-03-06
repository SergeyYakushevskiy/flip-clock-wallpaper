[Setup]
AppName=FlipClock Live Wallpaper
AppVersion=1.0
DefaultDirName={autopf}\FlipClockWallpaper
DefaultGroupName=Digital Live Wallpaper
UninstallDisplayIcon={app}\FlipClockWallpaper.exe
Compression=lzma2
SolidCompression=yes
OutputDir=setup_output
OutputBaseFilename=flipclock_wallpaper
SetupIconFile=assets\icons\app_icon.ico

PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline dialog

[Dirs]
Name: "{userappdata}\FlipClockWallpaper"; Permissions: users-full

[Files]
; Основной exe после сборки PyInstaller
Source: "dist\FlipClockWallpaper.exe"; DestDir: "{app}"; Flags: ignoreversion
; Иконка приложения
Source: "assets\icons\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Конфиг
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion

; Шрифты
Source: "assets\fonts\digital_7italic.ttf"; DestDir: "{autofonts}"; FontInstall: "Digital-7 Italic"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\digital_7mono.ttf"; DestDir: "{autofonts}"; FontInstall: "Digital-7 Mono"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\digital_7.ttf"; DestDir: "{autofonts}"; FontInstall: "Digital-7"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\Helvetica-Neue Cond Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Helvetica Neue Cond Bold"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\Helvetica-Neue Cond.ttf"; DestDir: "{autofonts}"; FontInstall: "Helvetica Neue Cond"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\RobotoCondensed-BoldItalic.ttf"; DestDir: "{autofonts}"; FontInstall: "Roboto Condensed Bold Italic"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\RobotoCondensed-Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Roboto Condensed Bold"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\RobotoCondensed-Italic.ttf"; DestDir: "{autofonts}"; FontInstall: "Roboto Condensed Italic"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\RobotoCondensed-LightItalic.ttf"; DestDir: "{autofonts}"; FontInstall: "Roboto Condensed Light Italic"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\RobotoCondensed-Light.ttf"; DestDir: "{autofonts}"; FontInstall: "Roboto Condensed Light"; Flags: onlyifdestfileexists uninsneveruninstall
Source: "assets\fonts\RobotoCondensed-Regular.ttf"; DestDir: "{autofonts}"; FontInstall: "Roboto Condensed Regular"; Flags: onlyifdestfileexists uninsneveruninstall

[Icons]
Name: "{group}\FlipClockWallpaper"; Filename: "{app}\FlipClockWallpaper.exe"
; Автозагрузка для текущего пользователя
Name: "{userstartup}\FlipClock Live Wallpaper"; Filename: "{app}\FlipClockWallpaper.exe"; WorkingDir: "{userappdata}\FlipClockWallpaper"
; Ярлык для папки настроек
Name: "{group}\Открыть папку настроек"; Filename: "explorer.exe"; Parameters: "{userappdata}\FlipClockWallpaper"

[Run]
Filename: "{app}\FlipClockWallpaper.exe"; Description: "Запустить обои сейчас"; Flags: nowait postinstall skipifsilent