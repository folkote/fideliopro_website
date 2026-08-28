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
- [ ] Independent review completed.
- [ ] Scoped commit pushed.
- [ ] Immutable `fideliopro_app` image built from the commit.
- [ ] Existing container retained as rollback and only `fideliopro_app` replaced.
- [ ] Health, image identity and all four public HTTPS URLs verified.
- [ ] Final SQL copies and `RevLabExport.exe` packaged for download.
