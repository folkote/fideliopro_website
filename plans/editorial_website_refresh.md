# Editorial website refresh and fiscal-case correction

## Approved scope
- Correct fiscal case: initial configuration of agent remuneration, then tested sale/refund. User meant setup from scratch, not zero-valued remuneration. Public wording: «Настроили агентское вознаграждение в Suite8». Existing pilot/legal limitations remain.
- More businesslike website, less rounded cards, original generated graphics. No backend/API/SQL/schema/dependency or mailbox changes.

## Design decisions
Surface: Decide/Learn, a B2B hotel-system service website, not a product dashboard.
- Restrained navy and teal, flat surfaces, 4–8px corners, no glow/glass/pill buttons.
- Smaller headline scale, stronger reading hierarchy. Services as a two-column ruled index, cases as horizontal illustrated stories on a contrasting paper background, detailed cases in readable columns.
- Cases moved after services to show evidence earlier. Existing products, contact channels, locales, legal text, calculator and metadata retained.
- Four original lightweight SVGs: isometric hotel/systems, archive restoration, missing export, agent configuration. Conceptual process art, no invented UI/metrics/customer data. Existing secondary illustrations retained and visually subdued.
- Five HTML pages share additive `css/editorial.css?v=1`; legacy base CSS left unchanged. Specific case-link labels and visible keyboard focus; mobile menu and detail-page contact remain available.

## Acceptance already exercised
- RED: new suite failed on old fiscal wording, missing editorial stylesheet/assets and generic case links.
- GREEN: 4 editorial tests + 3 existing case-publication tests; 5 SQL regressions.
- Existing Docker Playwright image used with `--network none`, readonly website mount and an in-container static server; 25 page/viewport combinations (root/RU/EN/ES/cases × 320/390/820/1060/1440) passed image loading, one H1, no document/header overflow, corner radii <=8, mobile menu open/close and fiscal anchor navigation. Zero page errors.
- Screenshots reviewed: desktop hero and case index; mobile home and case detail. Mobile text wrapping improved after review; final browser matrix rerun passed.
- Illustration XML/size/external-content checks passed. Graphics are not fake product screens.
- Audit before repair: excessive gradients/glass, equal tile grids, rounded icon decorations. After repair: primary composition and treatment replaced; inherited secondary technical art remains, no new stats/testimonials/claims.

## Verified release
- Independent source review PASS; all 11 reviewed source fingerprints matched before committing. Final-source 25-combination browser matrix rerun passed after mobile wrapping refinements. Reproducible check is committed as `tests/browser_editorial_check.py` (mount website at `/website`, script at `/check.py`, writable evidence at `/evidence`; run with existing `admin-next-playwright-python:1.58.0`, `--network none`, `--shm-size 256m`, `--entrypoint python ... /check.py`).
- Source commit `0d24382bd22451c0c8772ed7ebb14ed18fa0fd84` pushed to origin/main. Immutable image `fideliopro-editorial:0d24382bd22451c0c8772ed7ebb14ed18fa0fd84`, image ID `sha256:35985932d0fba018c68aa881f872e59b97b145a82d2576a7788814530cd15d6e`.
- Release used the previously reviewed switch pattern, fresh exact identities/parity files, extended byte smoke for all locale pages/new CSS/all SVGs. Full configuration, normalized HostConfig, mounts, network aliases, image and health checks passed. Previous container retained stopped as `fideliopro_app_rollback_editorial`; older `fideliopro_app_rollback_cases` also remains stopped. Account for retained Compose labels on future reconciliation.
- Public HTTPS readback passed: root, RU/EN/ES, case page, editorial stylesheet, all four graphics, unchanged calculator. Public SQL bytes unchanged. Full app/scripts/SQL runtime hash parity passed before and after.
- Public browser repeated at 1440 and 390 across all five pages: 10 combinations passed; new CSS/all images loaded, one H1, corrected fiscal heading, <=8px card radii, no horizontal overflow. Prior isolated screenshots were also visually reviewed, not just DOM-tested.
- Application healthy, zero restarts; no unrelated service replaced. `support@fidelio.pro` delivery remains untested as agreed.

## Notes
`support@fidelio.pro` remains displayed, mailbox setup is user's later task. Broader conversion/SEO/form/service-page work is outside this release. Do not alter unrelated untracked docker-compose.override.yml.
