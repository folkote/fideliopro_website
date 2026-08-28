from pathlib import Path


SQL_DIR = Path(__file__).parents[1] / "static" / "sql" / "revlab"


def read_sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8").lower()


def test_revlab_sql_set_has_four_mode_files():
    assert {path.name for path in SQL_DIR.glob("*.sql")} == {
        "select.sql",
        "selectBlocks.sql",
        "selectRecent.sql",
        "selectBlocksRecent.sql",
    }


def test_reservation_modes_use_business_date_and_short_category_code():
    full_sql = read_sql("select.sql")
    recent_sql = read_sql("selectRecent.sql")

    assert "ycat_shortdesc || ' ' || ycat_longdesc" not in full_sql
    assert "ycat_shortdesc || ' ' || ycat_longdesc" not in recent_sql
    assert "yres_expdeptime <= add_months(trunc(v8_sys_fideliodate), 12)" in full_sql
    assert "yres_expdeptime >= add_months(trunc(v8_sys_fideliodate), -1)" in recent_sql
    assert "yres_expdeptime <= add_months(trunc(v8_sys_fideliodate), 12)" in recent_sql


def test_blocks_modes_keep_zero_grid_and_bound_business_dates():
    full_sql = read_sql("selectBlocks.sql")
    recent_sql = read_sql("selectBlocksRecent.sql")

    for sql in (full_sql, recent_sql):
        assert "from wdat, ycat" in sql
        assert "nvl(" in sql
        assert "ycat_shortdesc || ' ' || ycat_longdesc" not in sql
        assert "add_months(trunc(v8_sys_fideliodate), 12)" in sql

    assert "select min(trunc(ydet_date)) from ydet" in full_sql
    assert "select min(trunc(ybld_date)) from ybld" in full_sql
    assert "select min(trunc(zpos_postdate)) from zpos" in full_sql
    assert "add_months(trunc(v8_sys_fideliodate), -1)" in recent_sql


def test_blocks_group_other_revenue_uses_other_stats_types():
    for name in ("selectBlocks.sql", "selectBlocksRecent.sql"):
        sql = read_sql(name)
        final_metric = sql.rsplit("|| ';' ||", 1)[1]
        assert "zdco_stats_type > 2" in final_metric


def test_blocks_queries_do_not_require_hotel_specific_combined_view():
    for name in ("selectBlocks.sql", "selectBlocksRecent.sql"):
        sql = read_sql(name)
        assert "m_zpos_ypos" not in sql
        assert "from zpos" in sql
        assert "from ypos" in sql
        assert "ypos_date" in sql
