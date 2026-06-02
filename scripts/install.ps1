[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$TargetSkills = "",
    [switch]$SkipPackage,
    [switch]$SkipSkills,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "command failed: $FilePath $($Arguments -join ' ')"
    }
}

function Invoke-SkillInstall {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonPath,
        [switch]$Preview
    )

    $arguments = @("scripts\install_skills.py")
    if ($TargetSkills) {
        $arguments += @("--target", $TargetSkills)
    }
    if ($Preview) {
        $arguments += "--dry-run"
    }
    Invoke-Checked -FilePath $PythonPath -Arguments $arguments
}

Push-Location $Root
try {
    if ($DryRun) {
        if (-not $SkipPackage) {
            Write-Output "dry-run: would create or refresh .venv"
            Write-Output "dry-run: would install the package with pip install -e ."
        }
        if (-not $SkipSkills) {
            Invoke-SkillInstall -PythonPath $Python -Preview
        }
        return
    }

    if (-not $SkipPackage) {
        Invoke-Checked -FilePath $Python -Arguments @("-m", "venv", ".venv")
        $VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
        Invoke-Checked -FilePath $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
        Invoke-Checked -FilePath $VenvPython -Arguments @("-m", "pip", "install", "-e", ".")
    }
    else {
        $VenvPython = $Python
    }

    if (-not $SkipSkills) {
        Invoke-SkillInstall -PythonPath $VenvPython
    }

    Write-Output "installed cellular-modem-control"
}
finally {
    Pop-Location
}
