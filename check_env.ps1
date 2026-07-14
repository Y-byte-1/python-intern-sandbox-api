$ErrorActionPreference = "Continue"

function Section {
    param([string]$Name)
    Write-Output ""
    Write-Output ("=" * 70)
    Write-Output $Name
    Write-Output ("=" * 70)
}

function Check-Command {
    param([string]$Name)

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        Write-Output "[MISSING] $Name"
        return $false
    }

    Write-Output "[FOUND] $Name"
    Write-Output "Path: $($cmd.Source)"
    return $true
}

Section "1. SYSTEM AND DISKS"

Get-ComputerInfo |
    Select-Object WindowsProductName, WindowsVersion, OsBuildNumber, OsArchitecture |
    Format-List

Get-PSDrive -PSProvider FileSystem |
    Select-Object Name,
        @{Name="UsedGB";Expression={[math]::Round($_.Used / 1GB, 2)}},
        @{Name="FreeGB";Expression={[math]::Round($_.Free / 1GB, 2)}},
        Root |
    Format-Table -AutoSize

Section "2. PYTHON AND CONDA"

$hasPython = Check-Command "python"
$hasPy = Check-Command "py"
$hasConda = Check-Command "conda"

if ($hasPython) {
    Write-Output ""
    Write-Output "python --version:"
    python --version

    Write-Output ""
    Write-Output "Python executable:"
    python -c "import sys; print(sys.executable)"

    Write-Output ""
    Write-Output "pip version:"
    python -m pip --version

    Write-Output ""
    Write-Output "Selected Python packages in the current environment:"
    $packages = @(
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "alembic",
        "uvicorn",
        "pytest",
        "ruff",
        "black",
        "mypy",
        "httpx",
        "asyncpg"
    )

    foreach ($pkg in $packages) {
        $version = & python -c "import importlib.metadata as m; print(m.version('$pkg'))" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Output ("[INSTALLED] {0} {1}" -f $pkg, $version)
        }
        else {
            Write-Output ("[NOT INSTALLED] {0}" -f $pkg)
        }
    }
}

if ($hasPy) {
    Write-Output ""
    Write-Output "py --version:"
    py --version

    Write-Output ""
    Write-Output "Registered Python installations:"
    py -0p
}

if ($hasConda) {
    Write-Output ""
    Write-Output "conda --version:"
    conda --version

    Write-Output ""
    Write-Output "Active Conda environment:"
    Write-Output $env:CONDA_DEFAULT_ENV

    Write-Output ""
    Write-Output "CONDA_PREFIX:"
    Write-Output $env:CONDA_PREFIX

    Write-Output ""
    Write-Output "Conda environments:"
    conda env list
}

Write-Output ""
Write-Output "where.exe python:"
where.exe python

Write-Output ""
Write-Output "where.exe py:"
where.exe py 2>$null

Section "3. GIT"

$hasGit = Check-Command "git"
if ($hasGit) {
    git --version

    Write-Output ""
    Write-Output "Git user.name:"
    git config --global user.name

    Write-Output ""
    Write-Output "Git user.email:"
    git config --global user.email
}

Section "4. DOCKER AND WSL"

$hasDocker = Check-Command "docker"
$hasWsl = Check-Command "wsl"

if ($hasDocker) {
    Write-Output ""
    Write-Output "Docker version:"
    docker --version

    Write-Output ""
    Write-Output "Docker Compose version:"
    docker compose version

    Write-Output ""
    Write-Output "Docker Engine status:"
    docker info
}

if ($hasWsl) {
    Write-Output ""
    Write-Output "WSL status:"
    wsl --status

    Write-Output ""
    Write-Output "WSL distributions:"
    wsl -l -v
}

Section "5. IDE AND API CLIENT"

Check-Command "code" | Out-Null
Check-Command "pycharm64.exe" | Out-Null
Check-Command "idea64.exe" | Out-Null

$hasWinget = Check-Command "winget"
if ($hasWinget) {
    Write-Output ""
    Write-Output "Installed Visual Studio Code:"
    winget list --name "Visual Studio Code"

    Write-Output ""
    Write-Output "Installed PyCharm:"
    winget list --name "PyCharm"

    Write-Output ""
    Write-Output "Installed IntelliJ IDEA:"
    winget list --name "IntelliJ IDEA"

    Write-Output ""
    Write-Output "Installed Postman:"
    winget list --name "Postman"

    Write-Output ""
    Write-Output "Installed Apifox:"
    winget list --name "Apifox"
}

Section "6. COMMON PORTS"

foreach ($port in @(8000, 5432, 6379)) {
    Write-Output ""
    Write-Output ("Port {0}:" -f $port)

    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($null -eq $connections) {
        Write-Output "[FREE OR NOT DETECTED]"
    }
    else {
        $connections |
            Select-Object LocalAddress, LocalPort, State, OwningProcess |
            Format-Table -AutoSize
    }
}

Section "7. SUMMARY RULES"

Write-Output "Python 3.11 or newer satisfies the written task requirement."
Write-Output "Use a project-local .venv instead of installing packages into Conda base."
Write-Output "Postman and Apifox are alternatives; only one is needed."
Write-Output "If docker --version works but docker info fails, Docker Desktop may not be running."
Write-Output "Keep the project and .venv on drive D when possible."