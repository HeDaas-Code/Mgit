@echo off
echo ========================================
echo MGit - ����ű�
echo ========================================
echo.

:: ������⻷��
if not exist venv\Scripts\python.exe (
    echo ����: δ�ҵ����⻷��
    echo ���ȴ������������⻷��
    exit /b 1
)

:: ���ͼ���ļ�
if not exist app.ico (
    echo ����: δ�ҵ�Ӧ��ͼ�� app.ico
    exit /b 1
)

:: ����Ƿ��Ѱ�װPyInstaller
if not exist venv\Scripts\pyinstaller.exe (
    echo ���ڰ�װPyInstaller...
    venv\Scripts\pip.exe install pyinstaller
)

:: ����ɵĹ�������
if exist build (
    echo ��������ɵ�buildĿ¼...
    rmdir /s /q build
)
if exist dist (
    echo ��������ɵ�distĿ¼...
    rmdir /s /q dist
)

:: ִ�д��
echo.
echo ���ڴ��Ӧ��...
venv\Scripts\pyinstaller.exe --clean MGit.spec

:: �����
if not exist dist\MGit.exe (
    echo.
    echo ���ʧ��!
    exit /b 1
)

echo.
echo ========================================
echo ����ɹ�! �����ļ�: dist\MGit.exe
echo ========================================

exit /b 0 