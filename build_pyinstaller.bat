echo Build app with PyInstaller 4.0
echo create dist/ build/

:: Build app
:: -w window mode
pyinstaller proxyui.py -w --onefile