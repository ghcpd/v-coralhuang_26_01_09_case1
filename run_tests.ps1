param()

$venv = ".venv_test"
$python = "python"

Write-Host "Creating virtual environment in $venv"
& $python -m venv $venv

Write-Host "Installing test dependencies"
& "$venv\Scripts\python.exe" -m pip install -q --upgrade pip
& "$venv\Scripts\python.exe" -m pip install -q pytest

Write-Host "Running tests"
& "$venv\Scripts\python.exe" -m pytest -q

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Tests passed. See ARTIFACTS.md and artifacts/runtime_trace.txt"
exit 0
