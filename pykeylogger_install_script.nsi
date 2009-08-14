; Installer script for win32 PyKeylogger
; Author: Daniel Folkinshteyn (nanotube@users.sourceforge.net)
; Based on the StartMenu.nsi example script provided with the NSIS installation.
;
; NOTE: this .NSI script is intended for NSIS 2.38.
;

;--------------------------------
;Include Modern UI

    !include "MUI2.nsh"

;--------------------------------
;General

    !define PYKEYLOGGER_NAME "Simple Python Keylogger"
    !define PYKEYLOGGER_VERSION "1.0.4"
    !define PYKEYLOGGER_PUBLISHER "Daniel Folkinshteyn"
    !define PYKEYLOGGER_WEB_SITE "http://pykeylogger.sourceforge.net"
    !define PYKEYLOGGER_INSTALLDIR "PyKeylogger"
    !define PYKEYLOGGER_EXENAME "pykeylogger"

    ;Name and file
    Name "Simple Python Keylogger"
    OutFile "pykeylogger-${PYKEYLOGGER_VERSION}_win32_installer.exe"

    ;Default installation folder
    InstallDir "$PROGRAMFILES\${PYKEYLOGGER_INSTALLDIR}"

    ;Get installation folder from registry if available
    InstallDirRegKey HKCU "Software\${PYKEYLOGGER_INSTALLDIR}" ""

    ;Request application privileges for Windows Vista
    RequestExecutionLevel user
    
    ;Some more options
    SetCompressor lzma
    ShowInstDetails show
    ShowUninstDetails show
    
;--------------------------------
;Variables

    Var StartMenuFolder

;--------------------------------
;Interface Settings

    ;--------------------------------
    ;Program Icon
    !define MUI_ICON "pykeylogger-${PYKEYLOGGER_VERSION}\${PYKEYLOGGER_EXENAME}icon.ico"

;--------------------------------
;Pages

    ;;;;;;;;;;;;;;;;
    ; Install Pages
    
    ; Welcome page
    !define MUI_WELCOMEPAGE_TITLE "Install PyKeylogger"
    !define MUI_WELCOMEPAGE_TEXT "PyKeylogger is a free open source keylogger written in the python programming language, available under the terms of the GNU General Public License. $\n $\n $\nIf you have any questions or feedback, please feel free to visit the project site, ${PYKEYLOGGER_WEB_SITE}."
    !insertmacro MUI_PAGE_WELCOME
    
    ; License page
    !define MUI_LICENSEPAGE_BUTTON		"Next >"
    !define MUI_LICENSEPAGE_TEXT_BOTTOM	"PyKeylogger is licensed under the GPL, a license designed to guarantee your continued freedom to use and modify this software. You need /not/ accept the license merely to use this program - only if you wish to modify and redistribute it."
    !insertmacro MUI_PAGE_LICENSE "doc\LICENSE.txt"

    !insertmacro MUI_PAGE_COMPONENTS
    !insertmacro MUI_PAGE_DIRECTORY

    ;Start Menu Folder Page Configuration
    !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU" 
    !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\${PYKEYLOGGER_INSTALLDIR}" 
    !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"

    !insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

    !insertmacro MUI_PAGE_INSTFILES

    ;;;;;;;;;;;;;;;;;;;;
    ; Uninstall Pages
    
    ; Uninstall welcome page: warn about removing logs
    !define MUI_WELCOMEPAGE_TITLE "Uninstall PyKeylogger"
    !define MUI_WELCOMEPAGE_TEXT "You are about to completely remove PyKeylogger from your system. $\n $\n $\nNote that if you store the keylogger logs in the installation directory (the default log location), YOUR LOGS WILL ALSO BE DELETED."
    !insertmacro MUI_UNPAGE_WELCOME

    !insertmacro MUI_UNPAGE_CONFIRM
    !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections
    
    ;;;;;;;;;;;;;
    ;Files
    
    Section "Program Files" SecFiles

        SetOutPath "$INSTDIR"
        SetOverwrite try

        ; fancy stuff here - recursively get everything from this dir with /r flag,
        ; instead of listing every file like we used to. thank you, gaim.
        File /r ".\pykeylogger-${PYKEYLOGGER_VERSION}\*.*"

        ;Store installation folder
        WriteRegStr HKCU "Software\${PYKEYLOGGER_INSTALLDIR}" "" $INSTDIR

        ;Create uninstaller
        WriteUninstaller "$INSTDIR\Uninstall.exe"
        
        ; Create entry in Add/Remove programs
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}" "DisplayName" "PyKeylogger - Simple Python Keylogger"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}" "UninstallString" "$INSTDIR\Uninstall.exe"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}" "InstallLocation" "$INSTDIR"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}" "DisplayIcon" "$INSTDIR\${PYKEYLOGGER_EXENAME}.exe,0"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}" "DisplayVersion" "${PYKEYLOGGER_VERSION}"
        WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}" "NoModify" 1
        WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}" "NoRepair" 1
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}" "URLInfoAbout" "${PYKEYLOGGER_WEB_SITE}"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}" "HelpLink" "${PYKEYLOGGER_WEB_SITE}"
    
    SectionEnd

    ;;;;;;;;;;;;;
    ;Shortcuts

    Section "Start Menu Shortcuts" SecStartMenuShortcut
        SetOverwrite on
        !insertmacro MUI_STARTMENU_WRITE_BEGIN Application

            ;Create shortcuts
            CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
            CreateShortCut "$SMPROGRAMS\$StartMenuFolder\PyKeylogger.lnk" "$INSTDIR\${PYKEYLOGGER_EXENAME}.exe" " " "$INSTDIR\${PYKEYLOGGER_EXENAME}icon.ico" 0
            CreateShortCut "$SMPROGRAMS\$StartMenuFolder\PyKeylogger Debug Mode.lnk" "$INSTDIR\${PYKEYLOGGER_EXENAME}_debug.exe" "-d" "$INSTDIR\${PYKEYLOGGER_EXENAME}icon.ico" 0
            WriteIniStr "$INSTDIR\${PYKEYLOGGER_NAME} Website.url" "InternetShortcut" "URL" "${PYKEYLOGGER_WEB_SITE}"
            CreateShortCut "$SMPROGRAMS\$StartMenuFolder\PyKeylogger Website.lnk" "$INSTDIR\${PYKEYLOGGER_NAME} Website.url"
            CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall PyKeylogger.lnk" "$INSTDIR\Uninstall.exe"

        !insertmacro MUI_STARTMENU_WRITE_END

        SetOverwrite off
    SectionEnd

    Section /o "Desktop Shortcut" SecDesktopShortcut
        SetOverwrite on
        CreateShortCut "$DESKTOP\PyKeylogger.lnk" "$INSTDIR\${PYKEYLOGGER_EXENAME}.exe" " " "$INSTDIR\${PYKEYLOGGER_EXENAME}icon.ico" 0
        SetOverwrite off
    SectionEnd

;--------------------------------
;Descriptions

    ;Language strings
    LangString DESC_SecFiles ${LANG_ENGLISH} "Install Program Files."
    LangString DESC_SecStartMenuShortcut ${LANG_ENGLISH} "Create Start Menu Shortcuts."
    LangString DESC_SecDesktopShortcut ${LANG_ENGLISH} "Create Desktop Shortcut."

    ;Assign language strings to sections
    !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
        !insertmacro MUI_DESCRIPTION_TEXT ${SecFiles} $(DESC_SecFiles)
        !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenuShortcut} $(DESC_SecStartMenuShortcut)
        !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktopShortcut} $(DESC_SecDesktopShortcut)
    !insertmacro MUI_FUNCTION_DESCRIPTION_END
 
;--------------------------------
;Uninstaller Section

    Section "Uninstall"
        
        ; Shortcuts
        !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
        RMDir /r "$SMPROGRAMS\$StartMenuFolder"
        Delete "$DESKTOP\PyKeylogger.lnk"
        
        ; Main Install Directories
        RMDir /r "$INSTDIR"
        
        ; Registry  
        DeleteRegKey /ifempty HKCU "Software\${PYKEYLOGGER_INSTALLDIR}"
        ; Registry Add/Remove programs
        DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYKEYLOGGER_INSTALLDIR}"
        
        SetAutoClose false ; this lets us look at the uninstall log

    SectionEnd