$ErrorActionPreference = 'Stop'
$toolsDir = "$(Split-Path -Parent $MyInvocation.MyCommand.Definition)"
$version  = $env:ChocolateyPackageVersion
$url      = "https://github.com/hammadxcm/go-phantom/releases/download/v$version/phantom-windows.exe"

$packageArgs = @{
    packageName   = $env:ChocolateyPackageName
    fileFullPath  = Join-Path $toolsDir 'phantom.exe'
    url           = $url
    checksum      = 'PLACEHOLDER_SHA256'
    checksumType  = 'sha256'
}

Get-ChocolateyWebFile @packageArgs
