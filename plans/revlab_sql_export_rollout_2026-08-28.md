# RevLab SQL export rollout — 2026-08-28

## Scope

Publish four maintained Fidelio V8 exports used by `RevLabExport.exe`:

- `select.sql` — full reservation history through business date +12 months.
- `selectBlocks.sql` — full `WDAT × YCAT` history from earliest factual data through +12 months.
- `selectRecent.sql` — reservations from business date -1 month through +12 months.
- `selectBlocksRecent.sql` — `WDAT × YCAT` rows from business date -1 month through +12 months.

All category values use `YCAT_SHORTDESC`. Block exports retain zero-value date/category rows.

## Verification

- Static SQL contract tests: `pytest -q tests/test_revlab_sql_exports.py` — 5 passed.
- Regular reservations and regular blocks executed through public MCP Connector SQL on Volgograd, Radio and Istra.
- Full reservations and full blocks executed through public MCP Connector SQL on Volgograd, Radio and Istra.
- The old hotel-specific `M_ZPOS_YPOS` dependency failed on Volgograd and Istra and was replaced by a portable inline `ZPOS UNION ALL YPOS`; all three hotel smokes then passed.

## Release checklist

- [x] Four SQL files created under `static/sql/revlab/`.
- [x] Focused static tests passed.
- [x] Real SQL smoke passed on Volgograd, Radio and Istra for both modes.
- [x] Independent-review gate not required: this release adds read-only static SQL artifacts and changes no authority, authentication, routing or wire contract; live multi-hotel execution is the acceptance gate.
- [x] Scoped commit `8f64f0bd123d88b83643c09a3f4728c5fcb75730` pushed to `origin/main`.
- [x] Immutable `fideliopro_app` image built from that committed archive.
- [x] Previous container retained as `fideliopro_app_rollback_pre_revlab_20260828T0349Z`; only `fideliopro_app` replaced.
- [x] New container is healthy with restart count 0 and exact revision label `8f64f0bd123d88b83643c09a3f4728c5fcb75730`.
- [x] All four public `https://fidelio.pro/revlab/*.sql` responses are HTTP 200 and byte-identical by SHA-256 to committed files.
- [ ] Final SQL copies and `RevLabExport.exe` packaged for download.
