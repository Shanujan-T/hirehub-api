$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$commits = @(
  @{ msg = "jwt optional middleware added"; files = @("app/middleware.py") },
  @{ msg = "community membership helpers updated"; files = @("app/controllers/community_controller.py") },
  @{ msg = "community mine route registered"; files = @("app/routes/community_routes.py") },
  @{ msg = "company controller logo upload updated"; files = @("app/controllers/company_controller.py") },
  @{ msg = "company model logo field updated"; files = @("app/models/company_model.py") },
  @{ msg = "company logo routes updated"; files = @("app/routes/company_routes.py") },
  @{ msg = "post controller image upload updated"; files = @("app/controllers/post_controller.py") },
  @{ msg = "post model image url field updated"; files = @("app/models/post_model.py") },
  @{ msg = "post image routes updated"; files = @("app/routes/post_routes.py") },
  @{ msg = "job model image url field updated"; files = @("app/models/job_model.py") },
  @{ msg = "image upload utility updated"; files = @("app/utils/image_upload.py") },
  @{ msg = "image posts seeder updated"; files = @("app/seeders/image_posts_seeder.py") },
  @{ msg = "community content seeder updated"; files = @("app/seeders/community_content_seeder.py") },
  @{ msg = "jobs seeder updated"; files = @("app/seeders/jobs_seeder.py") },
  @{ msg = "run seeders script updated"; files = @("run_seeders.py") },
  @{ msg = "sample post image asset added"; files = @("uploads/posts/16_office_setup.png") },
  @{ msg = "sample post image asset added"; files = @("uploads/posts/17_offer_celebration.png") },
  @{ msg = "sample post image asset added"; files = @("uploads/posts/18_hiring_banner.png") },
  @{ msg = "sample post image asset added"; files = @("uploads/posts/19_portfolio_guide.png") },
  @{ msg = "sample post image asset added"; files = @("uploads/posts/20_coworking_space.png") }
)

foreach ($c in $commits) {
  foreach ($f in $c.files) {
    if (Test-Path $f) { git add -- "$f" }
  }
  git commit -m $c.msg
}

Write-Host "API now has $(git rev-list --count HEAD) commits"
