# Grävlingarna — webbplats

## Viktiga regler
- **Testa alltid lokalt innan push.** Visa alltid ändringen i förhandsgranskningen och vänta på Miltons godkännande innan `git push` körs.
- Servern startas med `npx serve . -l 8080` i webbmappens rot.

## Struktur
- `index.html` — startsida
- `jobb.html` — jobbsida
- `assets/base.css` — delat designsystem
- `assets/photos/` — bilder i WebP-format
- `assets/videos/` — videor i MP4-format
- `assets/fonts/` — typsnitt

## Deploy
- `git push` → Netlify deployas automatiskt till gravlingarna.se (~30 sek)
- Reviews uppdateras automatiskt varje måndag via GitHub Actions

## Bildformat
- Alla bilder ska sparas som **WebP** (ej JPG/PNG) — originalen ignoreras av .gitignore
- Max 1200px på längsta sidan, kvalitet 83
