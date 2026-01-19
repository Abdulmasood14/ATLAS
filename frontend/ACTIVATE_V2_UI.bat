@echo off
echo ========================================
echo   ACTIVATING V2 ULTRA-MODERN UI
echo ========================================
echo.

cd /d "%~dp0src"

echo [1/5] Backing up V1 files...
if exist "app\page.tsx" move "app\page.tsx" "app\page_v1_backup.tsx" >nul
if exist "app\globals.css" move "app\globals.css" "app\globals_v1_backup.css" >nul
if exist "components\MessageBubble.tsx" move "components\MessageBubble.tsx" "components\MessageBubble_v1_backup.tsx" >nul
if exist "components\ChatWindow.tsx" move "components\ChatWindow.tsx" "components\ChatWindow_v1_backup.tsx" >nul
if exist "components\TypingIndicator.tsx" move "components\TypingIndicator.tsx" "components\TypingIndicator_v1_backup.tsx" >nul
echo    Done! (Backed up as *_v1_backup.tsx)

echo.
echo [2/5] Activating V2 page...
move "app\page_v2.tsx" "app\page.tsx" >nul
echo    Done!

echo.
echo [3/5] Activating V2 CSS...
move "app\globals_v2.css" "app\globals.css" >nul
echo    Done!

echo.
echo [4/5] Activating V2 components...
move "components\MessageBubble_v2.tsx" "components\MessageBubble.tsx" >nul
move "components\ChatWindow_v2.tsx" "components\ChatWindow.tsx" >nul
move "components\TypingIndicator_v2.tsx" "components\TypingIndicator.tsx" >nul
echo    Done!

echo.
echo [5/5] Cleaning up...
echo    All V2 files activated!

echo.
echo ========================================
echo   V2 UI SUCCESSFULLY ACTIVATED!
echo ========================================
echo.
echo Next steps:
echo   1. Restart your dev server: npm run dev
echo   2. Open http://localhost:3000
echo   3. Enjoy the ultra-modern UI!
echo.
echo To revert to V1:
echo   - Restore from *_v1_backup.tsx files
echo.
pause
