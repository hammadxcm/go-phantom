$ErrorActionPreference = 'SilentlyContinue'
$toolsDir = "$(Split-Path -Parent $MyInvocation.MyCommand.Definition)"
Remove-Item (Join-Path $toolsDir 'phantom.exe') -Force
