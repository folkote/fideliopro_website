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

## Pending release evidence
Record actual review, commit/build, live smoke and rollback identity after deployment. Broader commercial redesign, form, sitemap and service landing pages are outside this publication.
