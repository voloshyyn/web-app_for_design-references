param(
    [string]$Token = $env:GITHUB_TOKEN,
    [string]$Repo = "voloshyyn/web-app_for_design-references"
)

if (-not $Token) {
    Write-Error "GitHub Token is required. Set env:GITHUB_TOKEN or pass -Token."
    exit 1
}

$dataPath = Join-Path $PSScriptRoot "issues_data.json"
if (-not (Test-Path $dataPath)) {
    Write-Error "Data file $dataPath not found."
    exit 1
}

$rawJson = [System.IO.File]::ReadAllText($dataPath, [System.Text.Encoding]::UTF8)
$data = $rawJson | ConvertFrom-Json

$headers = @{
    "Authorization" = "token $Token"
    "Accept"        = "application/vnd.github.v3+json"
    "User-Agent"    = "SDD-Ticket-Automation-Script"
}

Write-Host "=== 1. Creating Labels for $Repo ===" -ForegroundColor Cyan
foreach ($lbl in $data.labels) {
    $url = "https://api.github.com/repos/$Repo/labels"
    $payload = @{
        name        = $lbl.name
        color       = $lbl.color
        description = $lbl.description
    } | ConvertTo-Json -Compress

    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
        $res = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $bytes -ContentType "application/json; charset=utf-8"
        Write-Host " [+] Created label: $($lbl.name)" -ForegroundColor Green
    } catch {
        if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::UnprocessableEntity) {
            Write-Host " [=] Label already exists: $($lbl.name)" -ForegroundColor Yellow
        } else {
            Write-Warning " [!] Label error $($lbl.name): $_"
        }
    }
}

Write-Host "`n=== 2. Creating Issues for $Repo ===" -ForegroundColor Cyan
$createdCount = 0

$tick = [char]96  # ASCII backtick

foreach ($task in $data.tasks) {
    $total_h = [math]::Round($task.ai_h + $task.human_h, 2)
    
    $bodyLines = @(
        "### Task Description (SDD Task ID: " + $task.id + ")",
        $task.notes,
        "",
        "---",
        "",
        "### Traceability Matrix",
        "- **SRS Requirements:** " + $tick + $task.req + $tick,
        "- **Ticket Type:** " + $tick + $task.type + $tick,
        "- **Predecessors in DAG:** " + $tick + $task.preds + $tick,
        "",
        "---",
        "",
        "### Roles and Labor Estimates",
        "- **Primary Assignee:** " + $tick + $task.role + $tick,
        "- **AI Agent Estimate:** " + $task.ai_h + " hrs",
        "- **Human Lead Estimate:** " + $task.human_h + " hrs",
        "- **Total Duration:** " + $total_h + " hrs",
        "",
        "---",
        "",
        "### SDD Engineering Execution Rules",
        "- **TDD Enforcement:** For Feature tickets, coding starts ONLY after the corresponding Test ticket is APPROVED.",
        "- **Stage-Gate Sovereignty:** For Gate tickets, transition decisions are strictly reserved for Human Lead (APPROVED or REVISE)."
    )
    $body = $bodyLines -join "`n"

    $payloadObj = @{
        title  = $task.title
        body   = $body
        labels = $task.labels
    }
    $payloadJson = $payloadObj | ConvertTo-Json -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($payloadJson)

    $issuesUrl = "https://api.github.com/repos/$Repo/issues"

    try {
        $res = Invoke-RestMethod -Uri $issuesUrl -Method Post -Headers $headers -Body $bytes -ContentType "application/json; charset=utf-8"
        Write-Host " [✔] Created Issue #$($res.number): $($task.title)" -ForegroundColor Green
        $createdCount++
        Start-Sleep -Milliseconds 600
    } catch {
        Write-Error " [✖] Failed to create $($task.id): $_"
    }
}

Write-Host "`n=== Finished: Successfully created $createdCount of $($data.tasks.Count) issues in $Repo! ===" -ForegroundColor Green
