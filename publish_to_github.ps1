# Upload a complete Aiko Desktop Pet source tree into an EXISTING repo.
# Safe behavior: clone current main, never force-push, preserve all remote history.
$ErrorActionPreference = 'Stop'
$repo = 'https://github.com/Lexoniarus/aiko-desktop-pet.git'
$source = (Resolve-Path -LiteralPath $PSScriptRoot).Path
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git for Windows is missing. Install from https://git-scm.com/downloads/win first.'
}
$target = Join-Path $env:TEMP ('aiko-github-publish-' + [guid]::NewGuid().ToString('N'))
Write-Host 'Cloning the current GitHub main branch...' -ForegroundColor Cyan
& git clone --branch main --single-branch $repo $target
if ($LASTEXITCODE -ne 0) { throw 'git clone failed. Repository was not changed.' }

$published = $false
try {
    $remote = (& git -C $target remote get-url origin).Trim()
    if ($remote -ne $repo) { throw ('Unexpected remote: ' + $remote) }
    # Disable global Windows CRLF conversion for this temporary clone only.
    & git -C $target config --local core.autocrlf false
    if ($LASTEXITCODE -ne 0) { throw 'git local line ending configuration failed' }
    Write-Host 'Copying source, sprite assets, tests and documentation...' -ForegroundColor Cyan
    & robocopy $source $target /E /XD '.git' '__pycache__' '.venv' '.pytest_cache' /XF '*.pyc' '*.pyo' '*.ttf' '*.otf' '*.zip' /NFL /NDL /NJH /NJS
    if ($LASTEXITCODE -gt 7) { throw ('robocopy failed (code ' + $LASTEXITCODE + ')') }

    # Work on copied text files only; never rewrite the user's source folder.
    # Trailing whitespace can make git diff --check reject an otherwise safe upload.
    Write-Host 'Normalizing trailing whitespace in copied text files...' -ForegroundColor Cyan
    $utf8 = [System.Text.UTF8Encoding]::new($false, $true)
    $textExtensions = @('.py', '.md', '.json', '.yml', '.yaml', '.txt', '.ps1', '.bat')
    $gitPrefix = (Join-Path $target '.git') + [IO.Path]::DirectorySeparatorChar
    foreach ($file in (Get-ChildItem -LiteralPath $target -File -Recurse)) {
        if ($file.FullName.StartsWith($gitPrefix, [StringComparison]::OrdinalIgnoreCase)) { continue }
        if (($file.Extension -notin $textExtensions) -and ($file.Name -ne '.gitignore') -and ($file.Name -ne '.gitattributes')) { continue }
        $original = [IO.File]::ReadAllText($file.FullName, $utf8)
        $clean = [regex]::Replace(
            $original,
            '[ \t]+(?=\r?$)',
            '',
            [Text.RegularExpressions.RegexOptions]::Multiline
        )
        if ($clean -cne $original) {
            [IO.File]::WriteAllText($file.FullName, $clean, $utf8)
            Write-Host ('Cleaned: ' + $file.Name) -ForegroundColor Yellow
        }
    }

    & git -C $target add -A
    if ($LASTEXITCODE -ne 0) { throw 'git add failed' }
    & git -C $target diff --cached --check
    if ($LASTEXITCODE -ne 0) { throw 'git diff check failed' }
    & git -C $target diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'Everything is already up to date.' -ForegroundColor Green
        exit 0
    }
    if ($LASTEXITCODE -ne 1) { throw 'Unable to check staged changes' }

    Write-Host 'Creating a normal commit (no history rewrite)...' -ForegroundColor Cyan
    & git -C $target commit -m 'feat: publish Aiko Desktop Pet v0.13'
    if ($LASTEXITCODE -ne 0) {
        throw 'Commit failed. Check Git user.name and user.email configuration.'
    }
    Write-Host 'Pushing to GitHub main (without force)...' -ForegroundColor Cyan
    & git -C $target push origin HEAD:main
    if ($LASTEXITCODE -ne 0) {
        throw ('Push rejected or auth required. Your staged clone is available at ' + $target)
    }
    Write-Host 'Success! https://github.com/Lexoniarus/aiko-desktop-pet' -ForegroundColor Green
    $published = $true
} finally {
    # Keep the temporary clone only when manual recovery is needed.
    if ($published) {
        Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue
    }
}
