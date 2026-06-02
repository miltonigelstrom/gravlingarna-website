# deploy.ps1 — Pusha alla ändringar till GitHub (Netlify deployas automatiskt)
$msg = Read-Host "Beskriv ändringen kort (t.ex. 'Uppdaterad kontaktsida')"
git add .
git commit -m $msg
git push
Write-Host ""
Write-Host "Klart! gravlingarna.se är uppdaterad inom 30 sekunder." -ForegroundColor Green
