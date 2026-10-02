# tools/enable-large-pages.ps1
# Grant 'SeLockMemoryPrivilege' (Lock Pages in Memory) to Administrators on Windows 11
# This unlocks 2MB Large Pages in Strata, shrinking 6.29 million 4KB page table entries down to 12,000 2MB large pages!

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Strata Windows 11 Large Pages Optimizer (2MB HugePages)   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[!] Error: Administrator privilege is required to assign user rights." -ForegroundColor Red
    Write-Host "    Please right-click PowerShell and choose 'Run as Administrator'." -ForegroundColor Yellow
    exit 1
}

$tempInf = [System.IO.Path]::Combine($env:TEMP, "strata_secpol.inf")
$tempSdb = [System.IO.Path]::Combine($env:TEMP, "strata_secpol.sdb")

try {
    Write-Host "[1/3] Exporting current Local Security Policy..." -ForegroundColor Green
    secedit /export /cfg $tempInf | Out-Null

    if (-not (Test-Path $tempInf)) {
        throw "Failed to export security template to $tempInf"
    }

    $content = Get-Content -Path $tempInf -Raw -Encoding Unicode
    if (-not $content) {
        $content = Get-Content -Path $tempInf -Raw
    }

    Write-Host "[2/3] Checking SeLockMemoryPrivilege..." -ForegroundColor Green
    if ($content -match "SeLockMemoryPrivilege\s*=\s*(.*)") {
        $currentPriv = $matches[1].Trim()
        if ($currentPriv -notmatch "\*S-1-5-32-544") {
            Write-Host "      Adding Administrators (*S-1-5-32-544) to existing privilege line..." -ForegroundColor Yellow
            $newPriv = $currentPriv + ",*S-1-5-32-544"
            $content = $content -replace "SeLockMemoryPrivilege\s*=.*", "SeLockMemoryPrivilege = $newPriv"
            Set-Content -Path $tempInf -Value $content -Encoding Unicode
        } else {
            Write-Host "      Administrators group (*S-1-5-32-544) is ALREADY granted SeLockMemoryPrivilege!" -ForegroundColor Green
        }
    } else {
        Write-Host "      Injecting SeLockMemoryPrivilege into [Privilege Rights]..." -ForegroundColor Yellow
        $content = $content -replace "\[Privilege Rights\]", "[Privilege Rights]`r`nSeLockMemoryPrivilege = *S-1-5-32-544"
        Set-Content -Path $tempInf -Value $content -Encoding Unicode
    }

    Write-Host "[3/3] Applying security policy..." -ForegroundColor Green
    secedit /configure /db $tempSdb /cfg $tempInf /areas USER_RIGHTS | Out-Null

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  SUCCESS! 'Lock Pages in Memory' granted to Administrators! " -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "NOTE: Windows requires a USER LOGOFF or SYSTEM RESTART for" -ForegroundColor Yellow
    Write-Host "      the privilege to populate into your active token." -ForegroundColor Yellow
    Write-Host "      After reboot, Strata will automatically use 2MB pages!" -ForegroundColor Yellow
    Write-Host ""
}
catch {
    Write-Host "[!] Error: $_" -ForegroundColor Red
}
finally {
    Remove-Item $tempInf -ErrorAction SilentlyContinue
    Remove-Item $tempSdb -ErrorAction SilentlyContinue
}
