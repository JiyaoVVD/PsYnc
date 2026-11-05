@echo off
setlocal

set "PROTOC=%~1"
if not defined PROTOC (
    for /f "delims=" %%P in ('where protoc.exe 2^>nul') do if not defined PROTOC set "PROTOC=%%P"
)
if not defined PROTOC set "PROTOC=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Google.Protobuf_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\protoc.exe"

if not exist "%PROTOC%" (
    echo protoc.exe was not found. Pass its full path as the first argument. 1>&2
    exit /b 1
)

pushd "%~dp0" || exit /b 1

rem Map the source directory to the generated Python package path.
"%PROTOC%" --proto_path=net/protos=net/proto_defs --python_out=. net/protos/types.proto net/protos/rpc.proto
set "RESULT=%ERRORLEVEL%"

popd
exit /b %RESULT%
