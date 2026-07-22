$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$commits = @(
  @{ msg = "user model notification fields added"; files = @("app/models/user_model.py") },
  @{ msg = "job model micro internship type added"; files = @("app/models/job_model.py") },
  @{ msg = "skill quiz model added"; files = @("app/models/skill_quiz_model.py") },
  @{ msg = "quiz attempt model added"; files = @("app/models/quiz_attempt_model.py") },
  @{ msg = "models init quiz imports added"; files = @("app/models/__init__.py") },
  @{ msg = "run.py schema alters for features updated"; files = @("run.py") },
  @{ msg = "whatsapp notifier service added"; files = @("app/services/__init__.py", "app/services/whatsapp_notifier.py") },
  @{ msg = "distance haversine utility added"; files = @("app/utils/distance.py") },
  @{ msg = "geocoding utility added"; files = @("app/utils/geocoding.py") },
  @{ msg = "job match notifier utility added"; files = @("app/utils/job_match_notifier.py") },
  @{ msg = "profile completion utility added"; files = @("app/utils/profile_completion.py") },
  @{ msg = "feature controller quiz and prefs added"; files = @("app/controllers/feature_controller.py") },
  @{ msg = "auth controller profile geocoding added"; files = @("app/controllers/auth_controller.py") },
  @{ msg = "dashboard controller completion score added"; files = @("app/controllers/dashboard_controller.py") },
  @{ msg = "job controller salary insights added"; files = @("app/controllers/job_controller.py") },
  @{ msg = "dashboard routes notification prefs added"; files = @("app/routes/dashboard_routes.py") },
  @{ msg = "job routes insights and optional jwt added"; files = @("app/routes/job_routes.py") },
  @{ msg = "skill routes quiz endpoints added"; files = @("app/routes/skill_routes.py") },
  @{ msg = "quiz seeder added"; files = @("app/seeders/quiz_seeder.py") },
  @{ msg = "run seeders quiz step added"; files = @("run_seeders.py") },
  @{ msg = "env example twilio vars added"; files = @(".env.example") },
  @{ msg = "readme differentiator features documented"; files = @("README.md") }
)

$created = 0
foreach ($c in $commits) {
  $added = $false
  foreach ($f in $c.files) {
    if ((Test-Path $f) -and (git status --porcelain -- "$f")) {
      git add -- "$f"
      $added = $true
    }
  }
  if ($added) {
    git commit -m $c.msg
    $created++
  }
}

Write-Host "Created $created API commits ($(git rev-list --count HEAD) total)"
