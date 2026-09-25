[CmdletBinding()]
param(
    [string]$Repo = 'kwiscion/machinekind-matura',
    [switch]$Publish
)

$ErrorActionPreference = 'Stop'

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$GitArgs)
    $result = & git -c "safe.directory=$script:RepoRoot" @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) { throw "git $($GitArgs -join ' ') failed: $($result -join "`n")" }
    return ($result -join "`n").Trim()
}

function Invoke-GhJson {
    param([Parameter(Mandatory)][string[]]$GhArgs)
    $result = & gh @GhArgs 2>&1
    if ($LASTEXITCODE -ne 0) { throw "gh $($GhArgs -join ' ') failed: $($result -join "`n")" }
    $joined = $result -join "`n"
    if (-not $joined) { return $null }
    return $joined | ConvertFrom-Json
}

function Get-AllIssues {
    $pages = Invoke-GhJson @('api', '--paginate', '--slurp', "repos/$Repo/issues?state=all&per_page=100")
    $items = @()
    foreach ($page in @($pages)) {
        foreach ($issue in @($page)) {
            if ($null -ne $issue -and $null -eq $issue.pull_request) { $items += $issue }
        }
    }
    return $items
}

function Find-ExistingIssue {
    param([object[]]$Issues, [string]$Key, [string]$Title)
    $marker = "<!-- overnight:$Key -->"
    $matches = @($Issues | Where-Object { $_.title -ceq $Title -or ([string]$_.body).Contains($marker) })
    if ($matches.Count -gt 1) { throw "Multiple issues match key '$Key' or exact title '$Title'; resolve duplicates manually." }
    if ($matches.Count -eq 1) { return $matches[0] }
    return $null
}

function Get-AllowedPaths {
    $paths = @('README.md', 'AGENTS.md', 'SOURCE.md', '.gitignore', 'agentsLog/README.md', 'scripts/publish_overnight.ps1')
    if (Test-Path -LiteralPath 'docs/overnight') {
        $paths += Get-ChildItem -LiteralPath 'docs/overnight' -File -Recurse | ForEach-Object {
            [IO.Path]::GetRelativePath($script:RepoRoot, $_.FullName).Replace('\', '/')
        } | Where-Object { $_ -notin @('docs/overnight/PUBLISHED.json', 'docs/overnight/ISSUE_LINKS.md') }
    }
    return @($paths | Sort-Object -Unique)
}

function Commit-And-PushScopedFiles {
    $branch = Invoke-Git @('branch', '--show-current')
    if ($branch -cne 'main') { throw "Refusing publication from branch '$branch'; expected main." }
    $origin = Invoke-Git @('remote', 'get-url', 'origin')
    if ($origin -notmatch 'github\.com[:/]kwiscion/machinekind-matura(?:\.git)?$') {
        throw "Origin '$origin' does not identify the intended repository kwiscion/machinekind-matura."
    }

    $allowed = Get-AllowedPaths
    $staged = @((Invoke-Git @('diff', '--cached', '--name-only')) -split "`n" | Where-Object { $_ })
    $outside = @($staged | Where-Object { $_ -notin $allowed })
    if ($outside.Count) { throw "Refusing to continue because unrelated paths are already staged: $($outside -join ', ')" }

    $existingChanges = @((Invoke-Git @('status', '--porcelain')) -split "`n" | Where-Object { $_ })
    if ($existingChanges.Count) {
        $stageArgs = @('add', '--') + $allowed
        [void](Invoke-Git $stageArgs)
        $nowStaged = @((Invoke-Git @('diff', '--cached', '--name-only')) -split "`n" | Where-Object { $_ })
        $outside = @($nowStaged | Where-Object { $_ -notin $allowed })
        if ($outside.Count) { throw "Refusing to commit paths outside the publication allowlist: $($outside -join ', ')" }
        if ($nowStaged.Count) {
            [void](Invoke-Git @('commit', '-m', 'Publish overnight issue packet'))
        }
    }

    [void](Invoke-Git @('fetch', 'origin', 'main'))
    $aheadBehind = Invoke-Git @('rev-list', '--left-right', '--count', 'HEAD...origin/main')
    $counts = $aheadBehind -split '\s+'
    if ($counts.Count -ne 2 -or [int]$counts[1] -ne 0) { throw "Local main is behind or diverged from origin/main ($aheadBehind); reconcile before publishing." }
    [void](Invoke-Git @('push', 'origin', 'main'))
}

$script:RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Push-Location $script:RepoRoot
try {
    $manifestPath = Join-Path $script:RepoRoot 'docs/overnight/issues/manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath)) { throw "Manifest not found: $manifestPath" }
    $manifest = @(Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json)
    if ($manifest.Count -ne 5) { throw "Expected exactly 5 issue records in the manifest; found $($manifest.Count)." }
    foreach ($item in $manifest) {
        foreach ($field in @('key', 'title', 'owner', 'file')) {
            if (-not $item.$field) { throw "Manifest item is missing '$field'." }
        }
        if ($item.key -notmatch '^[A-Za-z0-9._-]+$') { throw "Invalid key '$($item.key)' in manifest." }
        $resolvedBody = [IO.Path]::GetFullPath((Join-Path $script:RepoRoot ([string]$item.file)))
        if (-not $resolvedBody.StartsWith($script:RepoRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Issue body path escapes repository: $($item.file)"
        }
        if (-not (Test-Path -LiteralPath $resolvedBody -PathType Leaf)) { throw "Issue body file not found: $($item.file)" }
        $item | Add-Member -NotePropertyName ResolvedFile -NotePropertyValue $resolvedBody -Force
    }

    if (-not $Publish) {
        Write-Host "Dry run only. Validated five issue records for $Repo. Re-run with -Publish to push and publish."
        foreach ($item in $manifest) { Write-Host ("  {0}: {1}" -f $item.key, $item.title) }
        return
    }

    # gh auth status may report an inactive secondary account even when the active token works.
    $login = & gh api user --jq .login 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $login) { throw 'GitHub API authentication failed. Check the active gh account, then retry.' }
    $repoInfo = Invoke-GhJson @('api', "repos/$Repo")
    if ($repoInfo.full_name -cne $Repo) { throw "GitHub resolved a different repository: $($repoInfo.full_name)" }

    Commit-And-PushScopedFiles

    $issues = @(Get-AllIssues)
    $published = @()
    foreach ($item in $manifest) {
        $existing = Find-ExistingIssue -Issues $issues -Key ([string]$item.key) -Title ([string]$item.title)
        if ($existing) {
            $issue = $existing
            Write-Host ("Found existing issue for {0}: {1}" -f $item.key, $issue.html_url)
        } else {
            $body = Get-Content -LiteralPath $item.ResolvedFile -Raw
            $marker = "<!-- overnight:$($item.key) -->"
            if (-not $body.Contains($marker)) { $body = $body.TrimEnd() + "`n`n$marker`n" }
            if (-not $body.Contains("@$($item.owner)")) { $body = $body.TrimEnd() + "`n`nOwner: @$($item.owner)`n" }
            $tempBody = Join-Path ([IO.Path]::GetTempPath()) ("overnight-{0}-{1}.md" -f $item.key, [guid]::NewGuid().ToString('N'))
            try {
                Set-Content -LiteralPath $tempBody -Value $body -Encoding utf8
                $created = & gh issue create --repo $Repo --title ([string]$item.title) --body-file $tempBody --label overnight --label ready 2>&1
                if ($LASTEXITCODE -ne 0) {
                    # An ambiguous failure may have created the issue. Reconcile by marker/title, but never auto-retry creation.
                    $issues = @(Get-AllIssues)
                    $issue = Find-ExistingIssue -Issues $issues -Key ([string]$item.key) -Title ([string]$item.title)
                    if (-not $issue) { throw "Issue creation for '$($item.key)' failed; no matching issue was found. Retry the script after reviewing GitHub. Output: $($created -join "`n")" }
                    Write-Host ("Creation returned an error, but the issue exists for {0}: {1}" -f $item.key, $issue.html_url)
                } else {
                    $url = ($created | Select-Object -Last 1).Trim()
                    if ($url -notmatch '^https://github\.com/[^/]+/[^/]+/issues/\d+$') { throw "gh issue create returned an unexpected URL for '$($item.key)': $url" }
                    $number = [int]([regex]::Match($url, '/issues/(\d+)$').Groups[1].Value)
                    $issue = Invoke-GhJson @('api', "repos/$Repo/issues/$number")
                    if (-not $issue) { throw "Issue was created for '$($item.key)' but could not be read back. Re-run after reviewing GitHub." }
                    Write-Host ("Created issue for {0}: {1}" -f $item.key, $issue.html_url)
                }
            } finally {
                Remove-Item -LiteralPath $tempBody -Force -ErrorAction SilentlyContinue
            }
        }

        # Existing issues keep their current workflow labels; only ensure the project tag.
        $labelResult = & gh issue edit ([string]$issue.number) --repo $Repo --add-label overnight 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Warning "Issue $($issue.number) was found/published, but adding the overnight label failed." }
        $assigned = $false
        $assigneeCheck = & gh api "repos/$Repo/assignees/$($item.owner)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $assignResult = & gh issue edit ([string]$issue.number) --repo $Repo --add-assignee ([string]$item.owner) 2>&1
            if ($LASTEXITCODE -eq 0) { $assigned = $true }
            else { Write-Warning "Issue $($issue.number) is published; assignment to @$($item.owner) failed and remains pending." }
        } else {
            Write-Warning "Issue $($issue.number) is published; @$($item.owner) is not assignable in this repository. Owner mention is in the body; assignment remains pending. No invitation was sent."
        }
        $published += [pscustomobject]@{
            key = [string]$item.key
            url = [string]$issue.html_url
            number = [int]$issue.number
            owner = [string]$item.owner
            assigned = $assigned
        }
        # Keep the in-memory issue list current for duplicate detection during this run.
        $issues = @($issues | Where-Object { $_.number -ne $issue.number }) + $issue
    }

    $outDir = Join-Path $script:RepoRoot 'docs/overnight'
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
    $publishedPath = Join-Path $outDir 'PUBLISHED.json'
    $linksPath = Join-Path $outDir 'ISSUE_LINKS.md'
    $published | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $publishedPath -Encoding utf8
    $table = @('# Overnight issues', '', '| Key | Issue | Owner | Assignment |', '| --- | --- | --- | --- |')
    foreach ($row in $published) {
        $assignment = if ($row.assigned) { 'Assigned' } else { 'Pending' }
        $table += "| $($row.key) | [#$($row.number)]($($row.url)) | @$($row.owner) | $assignment |"
    }
    $table | Set-Content -LiteralPath $linksPath -Encoding utf8
    Write-Host "Publication results written to $publishedPath and $linksPath."
    # Publish only the generated tracking files in a second scoped commit.
    $trackingStaged = @((Invoke-Git @('diff', '--cached', '--name-only')) -split "`n" | Where-Object { $_ })
    if ($trackingStaged.Count) { throw "Unexpected staged files appeared during issue publication: $($trackingStaged -join ', ')" }
    [void](Invoke-Git @('add', '--', 'docs/overnight/PUBLISHED.json', 'docs/overnight/ISSUE_LINKS.md'))
    $trackingChanges = @((Invoke-Git @('diff', '--cached', '--name-only')) -split "`n" | Where-Object { $_ })
    if ($trackingChanges.Count) {
        [void](Invoke-Git @('commit', '-m', 'Record overnight issue links'))
        [void](Invoke-Git @('fetch', 'origin', 'main'))
        $aheadBehind = Invoke-Git @('rev-list', '--left-right', '--count', 'HEAD...origin/main')
        $counts = $aheadBehind -split '\s+'
        if ($counts.Count -ne 2 -or [int]$counts[1] -ne 0) { throw "Local main is behind or diverged from origin/main ($aheadBehind); tracking files were committed locally but not pushed." }
        [void](Invoke-Git @('push', 'origin', 'main'))
        Write-Host 'Tracking links committed and pushed to main.'
    } else {
        Write-Host 'Tracking links are unchanged; no follow-up commit was needed.'
    }
} finally {
    Pop-Location
}

