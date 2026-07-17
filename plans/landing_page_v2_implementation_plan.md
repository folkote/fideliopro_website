# Fidelio Pro Landing Page V2 — Implementation Plan

Date: 2026-07-17  
Owner: Architect  
Status: ready for Code handoff  
Primary specification: [landing_page_v2.md](landing_page_v2.md)

## 1. Purpose and Required Outcome

Update the main Fidelio Pro website landing page into a modern business-oriented dark corporate site for `fidelio.pro`.

The new landing must position Fidelio Pro as a company that helps hotels support, integrate, and modernize existing hotel IT systems without requiring a complete PMS replacement.

Core message:

> Развиваем Fidelio и Suite8 под задачи современного отеля.

The site must communicate:

- support for Fidelio V8 / Oracle Hospitality Suite8;
- troubleshooting and technical maintenance;
- additional modules and custom development;
- integrations with external systems;
- modern web interfaces on top of existing PMS infrastructure;
- reporting, dashboards, analytics, AI tools;
- Oracle Database, backups, monitoring, and infrastructure work.

## 2. User Decisions Already Confirmed

These decisions are fixed for implementation unless the Orchestrator explicitly changes them later:

1. Use static routing for the landing page and locale pages.
2. Keep the contact form/contact scenarios simple for the first implementation stage.
   - Do not design a complex backend contract.
   - Do not add advanced anti-spam architecture in the first stage.
   - Preserve simple Telegram/email contact flows.
3. Skip the task of confirming the final integrations list for now.
   - Do not block the landing implementation on integration-name verification.
   - Avoid unsupported marketing claims and do not invent partner/customer logos.
4. The wording about 24/7 support is acceptable as a universal message if written carefully.
   - Do not imply guaranteed SLA details that are not documented.
5. SVG illustrations must be separate files, not large inline SVG blocks inside HTML.

## 3. Current Project Architecture Summary

The Code agent does not need to reread the full Memory Bank before starting. Use this project context:

- Runtime: FastAPI application serving both API endpoints and static website files.
- Main landing page: [`static/website/index.html`](../static/website/index.html).
- Digital ID calculator page: [`static/website/digital-id-calculator.html`](../static/website/digital-id-calculator.html).
- Static router: [`app/routers/static_files.py`](../app/routers/static_files.py).
  - `/` reads [`static/website/index.html`](../static/website/index.html) and returns [`HTMLResponse`](../app/routers/static_files.py:46).
  - `/{filename:path}` serves `.html`, `.css`, `.js`, images, fonts, SQL files, and SVG assets through [`FileResponse`](../app/routers/static_files.py:192).
  - HTML files must render in the browser and must not be downloaded as attachments.
- Website assets live under [`static/website`](../static/website).
- Existing favicon/logo assets are under [`static/website/img`](../static/website/img) and [`static/website/images`](../static/website/images).
- The Digital ID calculator must remain available and must not be rewritten during the first Code task.

## 4. Implementation Principles

- Prefer static HTML/CSS/vanilla JS over a heavy frontend framework.
- Keep tasks small and independently reviewable.
- Preserve existing working public URLs and utility pages.
- Do not remove the Digital ID calculator link.
- Do not make broad router rewrites unless a specific locale-routing task requires it.
- Use a dark theme with corporate polish: dark navy/graphite backgrounds, light typography, controlled cyan/blue accents, gradients, glass-like cards, but no excessive visual noise.
- Avoid white visual dominance.
- Avoid stock hotel-room imagery as the main design language.
- Use system diagrams, abstract technology illustrations, interface-like cards, and hospitality process pictograms.
- Do not include real guest data, client data, credentials, internal database details, or unauthorized third-party logos.

## 5. Recommended File Structure

The implementation may adjust names slightly if justified, but this structure is recommended:

```text
static/website/
  index.html                         # Compatible root entrypoint; initially RU landing or redirect-free RU content
  ru/
    index.html                       # RU localized landing, added in locale task
  en/
    index.html                       # EN localized landing, added in locale task
  es/
    index.html                       # ES localized landing, added in locale task
  css/
    landing-v2.css                   # Dark design system and landing layout
  js/
    landing-v2.js                    # Optional lightweight interactions only
  locales/
    landing.ru.json                  # Optional if using static generation/light client locale data
    landing.en.json
    landing.es.json
  images/
    landing-v2/
      hero-system.svg
      service-support.svg
      service-modules.svg
      service-integrations.svg
      service-web-interfaces.svg
      service-analytics-ai.svg
      service-oracle-infra.svg
      solution-digital-id.svg
      solution-passport-scan.svg
      solution-reservation-profile.svg
      solution-web-companion.svg
      solution-integrations.svg
      solution-reports-dashboards.svg
      solution-backup-monitoring.svg
      solution-custom-development.svg
      architecture-modernization.svg
      advantage-hospitality-processes.svg
      advantage-existing-infrastructure.svg
      advantage-practical-solutions.svg
      advantage-after-launch-support.svg
      workflow-discovery.svg
      workflow-solution-design.svg
      workflow-development-testing.svg
      workflow-launch-support.svg
      partners-integration.svg
```

### HTML Structure Recommendation

Recommended sections for the new landing:

1. Header/navigation with logo, section anchors, contact CTA, language switch placeholder.
2. Hero with main headline, subtitle, two CTAs, and abstract hero SVG.
3. Services: six cards.
4. Solutions: eight cards, including Digital ID with calculator link.
5. Main advantage: modernization architecture scheme.
6. Why Fidelio Pro: four advantage cards.
7. Workflow: four steps.
8. Technology partners block.
9. Final CTA/contact block with Telegram, email, simple form or mailto scenario.
10. Footer with legal trademark disclaimer and preserved contact links.

### CSS Structure Recommendation

Use one landing-specific stylesheet for the new design:

- [`static/website/css/landing-v2.css`](../static/website/css/landing-v2.css)

Suggested internal CSS organization:

```css
/* 1. Design tokens */
/* 2. Base/reset additions */
/* 3. Layout primitives */
/* 4. Header and navigation */
/* 5. Hero */
/* 6. Cards and grids */
/* 7. Section-specific components */
/* 8. Contact/footer */
/* 9. Responsive breakpoints */
/* 10. Reduced motion and accessibility */
```

Suggested dark design tokens:

- Background base: `#07111f`, `#0b1628`, `#101b2e`.
- Elevated surfaces: translucent navy/graphite with subtle border.
- Primary accent: cyan/blue, e.g. `#38bdf8`, `#22d3ee`, `#2563eb`.
- Secondary accent: restrained violet/indigo only for gradients.
- Text primary: near-white, not pure white everywhere.
- Text muted: cool gray-blue.
- Border: low-opacity blue/cyan lines.
- Shadow: soft dark shadows plus low-opacity accent glow.

### JavaScript Recommendation

Only add [`static/website/js/landing-v2.js`](../static/website/js/landing-v2.js) if needed for:

- mobile menu toggle;
- smooth anchor handling;
- language switch navigation;
- simple form UX confirmation if the first implementation keeps a form.

The main SEO texts must be present in HTML and should not depend on JavaScript rendering.

## 6. Static Locale Model

Target locale URLs:

- `/ru/`
- `/en/`
- `/es/`
- `/` remains a compatible entrypoint.

Preferred model:

- `/` serves Russian content initially for backward compatibility.
- `/ru/`, `/en/`, `/es/` eventually serve static localized HTML pages.
- Language switcher links directly to the static locale URLs.
- Use `hreflang`, canonical URLs, localized title/description, Open Graph, and localized H1.

Allowed implementation options:

1. Separate static HTML pages:
   - [`static/website/index.html`](../static/website/index.html) for `/` compatibility.
   - `static/website/ru/index.html`, `static/website/en/index.html`, `static/website/es/index.html`.
   - May require a small router enhancement because current [`serve_static_file()`](../app/routers/static_files.py:99) rejects directory paths that are not files.
2. Lightweight static router enhancement:
   - Add support in [`app/routers/static_files.py`](../app/routers/static_files.py) for directory-style locale paths like `/ru/` mapping to `static/website/ru/index.html`.
   - Keep this small and explicit; do not introduce a frontend framework.
3. Locale JSON files plus static generation/manual HTML:
   - Locale JSON files may be used as content sources, but the deployed page should still expose SEO text in static HTML.

Do not implement heavy client-side routing, React/Vue SPA behavior, or runtime translation that leaves SEO text absent from HTML.

## 7. SVG Package Requirements

All SVG illustrations must be separate files under `static/website/images/landing-v2/`.

### Required SVG Files

Hero:

1. `hero-system.svg` — abstract PMS modernization ecosystem: Fidelio/Suite8 core, connector layer, web apps, integrations, reports, AI/analytics.

Six services:

2. `service-support.svg` — support and diagnostics for Fidelio/Suite8.
3. `service-modules.svg` — custom modules/business logic.
4. `service-integrations.svg` — data exchange and external systems.
5. `service-web-interfaces.svg` — browser/mobile interfaces.
6. `service-analytics-ai.svg` — reports, dashboards, AI insights.
7. `service-oracle-infra.svg` — Oracle DB, backups, infrastructure.

Eight solutions:

8. `solution-digital-id.svg` — QR/code-driven Digital ID check-in.
9. `solution-passport-scan.svg` — document scanning/recognition.
10. `solution-reservation-profile.svg` — guest reservation/self-service profile.
11. `solution-web-companion.svg` — web companion over existing PMS.
12. `solution-integrations.svg` — external integration hub.
13. `solution-reports-dashboards.svg` — reporting and management dashboards.
14. `solution-backup-monitoring.svg` — backup and monitoring.
15. `solution-custom-development.svg` — individual development.

Architecture scheme:

16. `architecture-modernization.svg` — visual scheme: Fidelio / Suite8 → Hotel Connector → Web apps, integrations, reports, AI.

Four advantages:

17. `advantage-hospitality-processes.svg` — knowledge of hotel operations.
18. `advantage-existing-infrastructure.svg` — working with existing infrastructure.
19. `advantage-practical-solutions.svg` — solving concrete business tasks.
20. `advantage-after-launch-support.svg` — implementation and post-launch support.

Four workflow steps:

21. `workflow-discovery.svg` — study the task.
22. `workflow-solution-design.svg` — propose solution.
23. `workflow-development-testing.svg` — develop and test.
24. `workflow-launch-support.svg` — launch and support.

Partners:

25. `partners-integration.svg` — vendors/partners connecting products to hotel systems.

### SVG Visual Rules

- Use consistent viewBox ratios where possible, e.g. `viewBox="0 0 320 220"` for cards and wider viewBox for hero/architecture.
- Use dark-transparent or no background so SVGs integrate into dark cards.
- Use shared accent palette: cyan, blue, restrained violet, muted gray-blue.
- Avoid large pure-white blocks.
- Use simple line icons, soft gradients, subtle glow, and lightweight geometric system nodes.
- Keep file sizes reasonable; avoid embedded raster images.
- Do not include real company logos unless explicitly approved.
- Do not include real guest names, reservation numbers, room numbers, database hostnames, credentials, or customer identifiers.
- Ensure SVGs scale cleanly at mobile card sizes.
- Add accessible `alt` text in HTML image tags; SVG files themselves may use `<title>` where practical.

## 8. Content Requirements for RU Baseline

The first implementation should use Russian copy from [landing_page_v2.md](landing_page_v2.md) as the source of truth.

### Hero

Headline:

> Развиваем Fidelio и Suite8 под задачи современного отеля

Subtitle:

> Поддержка, интеграции, веб-модули, отчётность и автоматизация — без полной замены вашей PMS.

Primary CTA:

> Обсудить задачу

Secondary CTA:

> Посмотреть решения

Support line:

> Fidelio V8 · Suite8 · Oracle · Интеграции · Web & Mobile · AI и аналитика

### Required Main Blocks

- Services: six cards from the source specification.
- Solutions: eight cards from the source specification.
- Main advantage block: “Не заменяем работающую систему — делаем её современной”.
- Why Fidelio Pro: four advantages.
- Workflow: four steps.
- Partner block: “Интегрируем ваши решения с гостиничными системами”.
- Final CTA: “Расскажите, какую задачу нужно решить”.

### Legal and Marketing Constraints

- Do not claim that Fidelio Pro is an official Oracle division or certified partner unless approved.
- Do not use Oracle or other third-party logos without permission.
- Footer should contain a neutral trademark disclaimer.
- Do not use fake client counts, fake testimonials, or “market leader” claims.
- Keep the 24/7 support wording generic and non-SLA-specific.

## 9. Acceptance Criteria for the Whole Landing V2 Workstream

Functional preservation:

- Telegram contact link is present and works.
- Email contact link is present and works.
- Link to [`digital-id-calculator.html`](../static/website/digital-id-calculator.html) is present in the Digital ID solution card or CTA.
- Existing favicon/logo behavior is preserved or intentionally replaced with equivalent branded assets.
- [`digital-id-calculator.html`](../static/website/digital-id-calculator.html) is not rewritten in the first RU landing task.

Static serving:

- `/` renders HTML in the browser.
- `/digital-id-calculator.html` renders HTML in the browser.
- HTML routes do not trigger file download behavior.
- SVG files are served as `image/svg+xml`.

Responsive and visual quality:

- No horizontal scroll from 320 px viewport width.
- Header/menu works on mobile.
- All critical text is readable on dark background.
- Cards and grids collapse cleanly on mobile.
- Main CTAs are visible above the fold on common desktop sizes.

SEO/accessibility:

- Page has one clear H1.
- Title and description match the RU SEO direction from [landing_page_v2.md](landing_page_v2.md).
- Main content is available without JavaScript.
- Images have meaningful `alt` attributes or are explicitly decorative.
- Interactive elements are keyboard reachable.
- Reduced-motion preferences are respected where animation is used.

## 10. Work Breakdown into Small Independent Code Tasks

Each task below should be suitable for a separate Code-mode assignment. Every task must end with a checkpoint summary listing changed files, manual checks, and any remaining risks.

### Task 1 — RU Landing Baseline and Dark Design System

Goal: implement only the base Russian version of the new landing and the dark design system.

Files/zones:

- [`static/website/index.html`](../static/website/index.html)
- [`static/website/css/landing-v2.css`](../static/website/css/landing-v2.css)
- existing logo/favicon references under [`static/website/img`](../static/website/img) or [`static/website/images`](../static/website/images)

Scope:

- Replace the current main landing markup with RU V2 structure.
- Add dark theme CSS tokens, layout, responsive grids, header, hero, cards, CTA, footer.
- Preserve Telegram, email, favicon/logo, and Digital ID calculator link.
- Add placeholders/references for future SVG files if actual SVG package is not part of this task.
- Do not implement `/ru/`, `/en/`, `/es/` routing yet.
- Do not rewrite [`digital-id-calculator.html`](../static/website/digital-id-calculator.html).
- Do not add backend contact-form logic.

Done when:

- `/` renders the RU landing.
- The visual direction is dark corporate, not white-dominant.
- All required RU sections are present.
- Telegram, email, and calculator links are visible and clickable.
- No horizontal scroll at 320 px.
- HTML is not downloaded as a file.

Checkpoint after task:

- Report changed files.
- Confirm preserved calculator link.
- Confirm contact links.
- Confirm mobile no-horizontal-scroll check.
- State that locales and SVG package are intentionally deferred.

### Task 2 — SVG Illustration Package

Goal: create the separate SVG files required by the plan.

Files/zones:

- `static/website/images/landing-v2/*.svg`
- [`static/website/index.html`](../static/website/index.html) only to connect images if needed
- [`static/website/css/landing-v2.css`](../static/website/css/landing-v2.css) only for image sizing if needed

Scope:

- Create all 25 SVG files listed in section 7.
- Keep visual language consistent.
- Replace placeholder icons/blocks in the RU landing with real SVG references.
- Add meaningful `alt` text in HTML.

Done when:

- All required SVG files exist as separate files.
- Landing uses the SVGs without inline large SVG blocks.
- SVGs render correctly on desktop and mobile.
- No unauthorized logos or sensitive data are present.

Checkpoint after task:

- List created SVG files.
- Confirm browser loads them as images.
- Confirm no horizontal scroll regression.

### Task 3 — Responsive Polish and Accessibility Pass

Goal: harden mobile behavior, keyboard accessibility, reduced motion, and contrast.

Files/zones:

- [`static/website/index.html`](../static/website/index.html)
- [`static/website/css/landing-v2.css`](../static/website/css/landing-v2.css)
- [`static/website/js/landing-v2.js`](../static/website/js/landing-v2.js) only if needed for mobile menu

Scope:

- Add/verify accessible mobile navigation.
- Ensure focus states are visible.
- Add `aria-label` where needed.
- Add `prefers-reduced-motion` handling.
- Tune breakpoints from 320 px upward.
- Avoid layout shift from images by specifying dimensions or aspect ratios.

Done when:

- Keyboard navigation reaches all menu links and CTAs.
- Mobile header/menu is usable.
- No horizontal scroll at 320 px, 360 px, 768 px, and desktop widths.
- Motion is disabled/reduced for users preferring reduced motion.

Checkpoint after task:

- Report tested viewport widths.
- Report any accessibility compromises if present.

### Task 4 — Static Locale Routing Model

Goal: introduce `/ru/`, `/en/`, `/es/` static locale paths while preserving `/`.

Files/zones:

- [`app/routers/static_files.py`](../app/routers/static_files.py)
- `static/website/ru/index.html`
- `static/website/en/index.html`
- `static/website/es/index.html`
- [`static/website/index.html`](../static/website/index.html)

Scope:

- Choose either separate static localized pages or a minimal router enhancement.
- Preserve `/` as compatible entrypoint.
- Add direct language switch links.
- Avoid heavy frontend frameworks and SPA routing.
- Keep SEO text static in HTML.

Done when:

- `/` renders.
- `/ru/` renders.
- `/en/` renders.
- `/es/` renders.
- Locale pages do not download as attachments.
- Existing `/digital-id-calculator.html` still renders.

Checkpoint after task:

- Report selected locale architecture.
- Report route checks and any router changes.

### Task 5 — EN and ES Content Pages

Goal: add professional English and Spanish localized landing content.

Files/zones:

- `static/website/en/index.html`
- `static/website/es/index.html`
- optional `static/website/locales/*.json`
- shared [`static/website/css/landing-v2.css`](../static/website/css/landing-v2.css)

Scope:

- Translate naturally, not literally.
- Keep layout parity with RU.
- Add locale-specific title, description, H1, Open Graph, canonical, and hreflang.
- Preserve contact links and calculator link where appropriate.

Done when:

- EN and ES pages render static SEO text.
- Language switcher works between RU/EN/ES and `/`.
- No layout break from longer Spanish/English strings.

Checkpoint after task:

- List localized pages updated.
- Confirm SEO tags and hreflang.

### Task 6 — Contact Block and Simple Form UX

Goal: preserve simple contact scenarios without over-engineering backend behavior.

Files/zones:

- landing HTML pages
- [`static/website/js/landing-v2.js`](../static/website/js/landing-v2.js) if used

Scope:

- Keep Telegram and email primary.
- If a form exists, use simple mail/contact behavior or existing mechanism only.
- Show a clear confirmation/error message for any client-side form interaction.
- Do not add a new complex backend API contract.
- Do not add advanced anti-spam implementation in this first stage.

Done when:

- User can contact via Telegram.
- User can contact via email.
- Any form behavior is understandable and does not silently fail.

Checkpoint after task:

- Report final contact mechanisms.
- Confirm no backend contract was introduced.

### Task 7 — SEO, Legal, and Static Serving Validation

Goal: final content/serving validation before release.

Files/zones:

- landing HTML pages
- [`app/routers/static_files.py`](../app/routers/static_files.py) only if static-serving issues remain

Scope:

- Verify title/description/Open Graph/canonical/hreflang.
- Verify trademark disclaimer.
- Verify no unauthorized Oracle/third-party logo use.
- Verify no HTML download regression.
- Verify Digital ID calculator remains reachable.
- Verify favicon/logo still work.

Done when:

- `/`, `/ru/`, `/en/`, `/es/`, and `/digital-id-calculator.html` render correctly.
- No `Content-Disposition: attachment` for HTML pages.
- Footer legal disclaimer exists.
- No unsupported claims or fake metrics/testimonials.

Checkpoint after task:

- Provide validation evidence and changed files.

### Task 8 — Deployment/Runtime Smoke Check

Goal: validate the landing on the running FastAPI service after deployment.

Role target: Debug or DevOps.

Scope:

- Check HTTP status and content type for `/`, `/digital-id-calculator.html`, SVG files, CSS, JS.
- Check locale paths if implemented.
- Check that HTML renders and is not downloaded.
- Check mobile viewport manually or with browser tooling.

Done when:

- Runtime smoke confirms static serving and links.
- Any deployment-only issue is documented with repro steps.

Checkpoint after task:

- Report URLs checked, status codes, content types, and any defects.

## 11. First Code Handoff — Mandatory Scope

The first Code assignment after this plan must be limited to:

> Implement only the base RU version of the new main landing and dark design system.

Allowed in first Code task:

- update [`static/website/index.html`](../static/website/index.html);
- create [`static/website/css/landing-v2.css`](../static/website/css/landing-v2.css);
- optionally create a tiny [`static/website/js/landing-v2.js`](../static/website/js/landing-v2.js) for mobile menu only;
- preserve existing logo/favicon/contact/calculator links;
- add image placeholders or reference future SVG paths if needed.

Not allowed in first Code task:

- do not implement multilingual routing;
- do not create all EN/ES pages;
- do not rewrite [`digital-id-calculator.html`](../static/website/digital-id-calculator.html);
- do not redesign backend contact APIs;
- do not make broad changes to [`app/routers/static_files.py`](../app/routers/static_files.py) unless fixing an immediate HTML rendering regression.

First Code task acceptance criteria:

- `/` shows the new RU dark landing.
- The page includes the hero, services, solutions, advantage, why-us, workflow, partner, and final CTA blocks.
- Telegram link exists.
- Email link exists.
- Digital ID calculator link points to [`digital-id-calculator.html`](../static/website/digital-id-calculator.html).
- Favicon/logo remains present.
- HTML renders in the browser, not as a download.
- There is no horizontal scroll from 320 px viewport width.
- Existing calculator page is untouched except for being linked from the new landing.

## 12. Suggested Handoff Prompt for Code Mode

Use this as the next Code-mode instruction:

```text
Implement Task 1 from plans/landing_page_v2_implementation_plan.md only.

Scope: create the base Russian V2 landing in static/website/index.html and a dark corporate design system in static/website/css/landing-v2.css. Add only minimal JS for mobile navigation if necessary. Preserve Telegram, email, logo/favicon, and the link to static/website/digital-id-calculator.html. Do not implement multilingual routing, do not create EN/ES pages, do not rewrite the calculator, and do not add backend contact-form logic.

Acceptance: / renders as HTML, dark design is not white-dominant, all RU sections are present, calculator/contact links work, favicon/logo remain, and no horizontal scroll exists from 320 px.
```

