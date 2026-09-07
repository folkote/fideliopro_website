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

## Release gates
Pending independent source review, commit/push, immutable static-only build from the current exact running image and committed website files. Fresh backend/scripts/SQL parity before and after; preserve previous container under a unique rollback name; use prior verified bounded switch with both-side Docker OomKillDisable normalization. Verify exact public HTML/CSS/SVG bytes, health/image/restarts, original calculator and SQL, browser rendering. Update with actual evidence after release.

## Notes
`support@fidelio.pro` remains displayed, mailbox setup is user's later task. Broader conversion/SEO/form/service-page work is outside this release. Do not alter unrelated untracked docker-compose.override.yml.
