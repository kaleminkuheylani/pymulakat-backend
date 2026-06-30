# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Ensure data directory exists
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
}

$LogFile = "data\cron.log"

# Log start time
"" | Out-File -FilePath $LogFile -Append -Encoding utf8
"=== Cron Job Started: $(Get-Date) ===" | Out-File -FilePath $LogFile -Append -Encoding utf8

try {
    # Check if uv is available
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        "Running with uv..." | Out-File -FilePath $LogFile -Append -Encoding utf8
        $out = uv run python services/gemini.py --generate-creative --count 5 --email kaleminkuheylani@gmail.com 2>&1
        $out | Out-File -FilePath $LogFile -Append -Encoding utf8
    } elseif (Test-Path ".venv\Scripts\python.exe") {
        "Running with .venv\Scripts\python..." | Out-File -FilePath $LogFile -Append -Encoding utf8
        $out = .venv\Scripts\python.exe services/gemini.py --generate-creative --count 5 --email kaleminkuheylani@gmail.com 2>&1
        $out | Out-File -FilePath $LogFile -Append -Encoding utf8
    } else {
        "Running with system python..." | Out-File -FilePath $LogFile -Append -Encoding utf8
        $out = python services/gemini.py --generate-creative --count 5 --email kaleminkuheylani@gmail.com 2>&1
        $out | Out-File -FilePath $LogFile -Append -Encoding utf8
    }
} catch {
    "Error executing script: $_" | Out-File -FilePath $LogFile -Append -Encoding utf8
}

"=== Cron Job Finished: $(Get-Date) ===" | Out-File -FilePath $LogFile -Append -Encoding utf8
