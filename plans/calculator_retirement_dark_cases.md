# Retire Digital ID calculator; unify dark case backgrounds

## Approved scope
Remove the situational calculator page and all public links, preserve Digital ID product description. User additionally rejected bright case backgrounds: case index and detailed sections now use the existing dark --bg-2 surface and inherited readable text/accent colors. CSS cache revision incremented to 2 across all five active pages.

## Verified source changes
- Deleted standalone calculator HTML (all its logic/styles were inline; referenced logo remains shared).
- Removed eight links across root/RU/EN/ES. No public HTML reference remains, including legacy non-UTF8 pages scanned as bytes. Historical plans remain historical; bundled third-party generic calculator icons are not this feature.
- RED: retirement/dark-surface tests failed against old source. GREEN: 11 unit checks plus five existing SQL checks passed.
- Chromium network-none static preview: 25 combinations (five pages by 320/390/820/1060/1440) passed, including computed dark backgrounds/text, absent calculator links, old URL404, responsive layouts and navigation. Actual screenshot reviewed: dark integrated appearance and readable content. Initial preview caught undefined --bg-soft; corrected to existing --bg-2 and reran successfully.

## Release gates
Pending independent review, commit/push and static-only immutable overlay. Overlay must explicitly delete inherited calculator file, not just omit COPY. Verify candidate absence, source-byte parity and unchanged backend/scripts/SQL. Reuse reviewed exact-identity switch; public calculator404 is mandatory, not merely missing links. Preserve previous stopped rollback. No backend/API/database changes, no unrelated container changes; keep untracked docker-compose.override.yml.
