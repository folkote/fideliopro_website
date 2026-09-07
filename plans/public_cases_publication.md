# Anonymized public case studies

## Approved scope
User approved three anonymized cases: training-schema data restore (not PMS GUI/disaster recovery), accounting missing-date CSV export (not accounting acceptance/future guarantees), fiscal sale/refund pilot (not mass acceptance/legal advice).
Publish cards on root and RU home and detailed `/cases.html`. Replace contact with `support@fidelio.pro` on current RU/EN/ES homes; Telegram remains primary. No mailbox configuration or submission form is included. No private source document, hotel names, internal IDs, quotes or screenshots may be published.

## Implementation and gates
- Reuse existing CSS; no backend, routes, SQL, dependency or API changes.
- `python3 -m unittest discover -s tests -p test_public_cases.py -v`: 3 tests passed (content boundaries, confidentiality, anchors/cards, contact locales).
- `git diff --check`: passed.
- Independent content/HTML review required before release.
- Build an immutable image FROM the exact existing production image, overlaying only the five committed public HTML files. This preserves all existing API code/dependencies/runtime content byte-for-byte.
- Preserve the previous container stopped under a rollback name, retaining its exact configuration. Clone current Docker configuration for the replacement; no environment values may be logged.
- Acceptance: public home/RU cards, detail anchors and limitations, EN/ES contact, calculator, static SQL sample parity, health and restart count; desktop/mobile DOM layout smoke.

## Verified production outcome
- Published revision `882d79c9fd1ffd4f9cc3b7e5519b129c16f9ba87`, pushed to origin/main; immutable static-only image `fideliopro-cases:882d79c9fd1ffd4f9cc3b7e5519b129c16f9ba87`, ID `sha256:b5613ea26e8be40463a34afab5d28ccd745296a838906909e75b4d347311749f`.
- Previous container retained stopped as `fideliopro_app_rollback_cases`. Account for its inherited Compose labels during future release reconciliation; it is not an active service.
- Independent HTML/content review and bounded switch review passed. Initial switch refused HostConfig mismatch and verified restoration of original ID, homepage and health. Isolated no-network/no-secret start experiment proved OomKillDisable null -> false at create -> null at start. Normalized only this equivalent default on both comparison sides; second switch passed configuration, mounts, network aliases and image identity gates.
- Publication tests: 3 passed. Existing SQL regression functions: 5 passed. Diff check passed.
- Public HTTPS root, RU/EN/ES, `/cases.html`, and calculator: HTTP 200 and exact source bytes. Existing public SQL bytes unchanged. All runtime app/scripts/SQL hashes unchanged; candidate parity proved before deployment.
- Browser DOM checks on root, RU and cases at 1280/390 widths: one H1, no horizontal overflow, no broken loaded images; three cards / three detail sections. Actual click reached `/cases.html#restore`. DOM/layout verification, not screenshot visual review.
- Final repeated public health healthy; current container healthy, restart count zero; startup complete, no traceback/error lines in checked new-container logs.
- Unrelated untracked `docker-compose.override.yml` preserved. No API/SQL/schema/dependency changes. Mailbox delivery unverified; user configures later, Telegram remains first contact action.
- Broader redesign, form, sitemap and service pages remain outside this publication.
