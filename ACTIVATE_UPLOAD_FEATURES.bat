@echo off
echo ========================================
echo   ACTIVATING UPLOAD STATUS FEATURES
echo ========================================
echo.
echo This will activate:
echo   1. Upload Status Widget with animations
echo   2. Dynamic Suggested Questions (Phi-4)
echo   3. Real-time progress tracking
echo.
pause
echo.

cd /d "%~dp0frontend\src\components"

echo [1/2] Backing up original components...
if exist "FileUpload.tsx" (
    copy /Y "FileUpload.tsx" "FileUpload_original_backup.tsx" >nul
    echo    - FileUpload.tsx backed up
)
if exist "ChatWindow.tsx" (
    copy /Y "ChatWindow.tsx" "ChatWindow_original_backup.tsx" >nul
    echo    - ChatWindow.tsx backed up
)
echo.

echo [2/2] Activating enhanced components...
if exist "FileUpload_enhanced.tsx" (
    copy /Y "FileUpload_enhanced.tsx" "FileUpload.tsx" >nul
    echo    - FileUpload_enhanced.tsx activated
)
if exist "ChatWindow_with_dynamic_questions.tsx" (
    copy /Y "ChatWindow_with_dynamic_questions.tsx" "ChatWindow.tsx" >nul
    echo    - ChatWindow_with_dynamic_questions.tsx activated
)
echo.

echo ========================================
echo   FEATURES ACTIVATED!
echo ========================================
echo.
echo Next steps:
echo   1. Restart backend:  py -3.11 backend\main.py
echo   2. Restart frontend: npm run dev
echo   3. Upload a PDF to test!
echo.
echo Features enabled:
echo   √ Upload status modal with animations
echo   √ Processing steps visualization
echo   √ Dynamic questions using Phi-4
echo   √ Company-specific suggestions
echo.
echo To revert: Restore from *_original_backup.tsx files
echo.
pause
