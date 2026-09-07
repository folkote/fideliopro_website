# Retire Digital ID calculator; unify dark case backgrounds

## Approved scope
Remove the situational calculator page and all public links, preserve Digital ID product description. User additionally rejected bright case backgrounds: case index and detailed sections now use the existing dark --bg-2 surface and inherited readable text/accent colors. CSS cache revision incremented to 2 across all five active pages.

## Verified source changes
- Deleted standalone calculator HTML (all its logic/styles were inline; referenced logo remains shared).
- Removed eight links across root/RU/EN/ES. No public HTML reference remains, including legacy non-UTF8 pages scanned as bytes. Historical plans remain historical; bundled third-party generic calculator icons are not this feature.
- RED: retirement/dark-surface tests failed against old source. GREEN: 11 unit checks plus five existing SQL checks passed.
- Chromium network-none static preview: 25 combinations (five pages by 320/390/820/1060/1440) passed, including computed dark backgrounds/text, absent calculator links, old URL404, responsive layouts and navigation. Actual screenshot reviewed: dark integrated appearance and readable content. Initial preview caught undefined --bg-soft; corrected to existing --bg-2 and reran successfully.

## Verified release
- Independent source review passed calculator removal and identified undefined --bg-soft. Corrected to --bg-2, updated tests, and reran the full 25-combination browser gate successfully before commit.
- Source `93955cb0181382c224ec41b0d979b9a66d57a2bd` committed and pushed. Immutable image `fideliopro-dark-retire:93955cb0181382c224ec41b0d979b9a66d57a2bd`, ID `sha256:ba242be78002be03d9023d5ca72bb83c39d6c9be7b4115b39dfcb2e65666ac5f`.
- Overlay explicitly removed inherited calculator HTML. Candidate scan verified no file or public HTML references; full backend/scripts/SQL byte parity passed before and after deployment.
- Exact-identity switch passed Config/HostConfig/mounts/network checks, zero restarts and health. Prior image retained stopped as `fideliopro_app_rollback_dark_retire`; account for older retained rollback containers and their Compose labels on later maintenance.
- Public HTTPS all five entry pages and stylesheet v2 match source bytes. Calculator URL returns404 with and without a query string. Runtime calculator file absent. Public health healthy.
- Live browser: 10 combinations (five pages x desktop/mobile) passed. Case index/details computed backgrounds rgb(16,29,43), foreground rgb(237,241,243); no calculator links, stylesheet v2 loaded, no overflow.
- No backend/API/database change or unrelated service replacement; untracked docker-compose.override.yml preserved.
