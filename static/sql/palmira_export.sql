SELECT csv_line
FROM (
  WITH
  -- 1) Агрегация продаж
  zpos_agg AS (
    SELECT
      z.zpos_postdate,
      d.ydet_xcma_id,
      z.zpos_zdco_id,
      SUM(z.zpos_grossunitprice * z.zpos_quantity) AS amount
    FROM zpos z
    JOIN yres y ON z.zpos_originated_yres_id = y.yres_id
    JOIN ydet d ON y.yres_last_ydet_id       = d.ydet_id
    GROUP BY
      z.zpos_postdate,
      d.ydet_xcma_id,
      z.zpos_zdco_id
  ),
  -- 2) Основная таблица
  base AS (
    SELECT
      x.xcma_longdesc,
      m.longdesc                               AS stat_longdesc,
      w.wdat_date,
      zd.zdco_numericdesc || ' ' || zd.zdco_longdesc AS depcode,
      zd.zdco_stats_type                       AS sort_order,
      SUM(zagg.amount)                         AS amount
    FROM wdat w
    JOIN zpos_agg zagg ON zagg.zpos_postdate = w.wdat_date
    JOIN xcma x        ON zagg.ydet_xcma_id  = x.xcma_id
    JOIN zdco zd       ON zagg.zpos_zdco_id  = zd.zdco_id
    JOIN m_statcode m  ON zd.zdco_stats_type = m.id
    WHERE
      zd.zdco_cdt = 1
      AND w.wdat_date BETWEEN TRUNC(SYSDATE, 'YYYY')
                          AND ADD_MONTHS(TRUNC(SYSDATE, 'YYYY'), 12) - (1/86400)
    GROUP BY
      x.xcma_longdesc,
      m.longdesc,
      w.wdat_date,
      zd.zdco_numericdesc,
      zd.zdco_longdesc,
      zd.zdco_stats_type
  ),
  -- 3) Список колонок (stat + depcode)
  cols AS (
    SELECT DISTINCT
      stat_longdesc,
      depcode,
      sort_order
    FROM base
  ),
  -- 4) Строки отчёта
  row_keys AS (
    SELECT DISTINCT
      xcma_longdesc,
      wdat_date
    FROM base
  )
  -- 5) Генерация CSV
  SELECT csv_line, ord, wdate, xdesc
  FROM (
    -- 5.1 Первая строка заголовка: stat_longdesc
    SELECT
      0 AS ord,
      NULL AS wdate,
      NULL AS xdesc,
      'xcma_longdesc;wdat_date;' ||
      LISTAGG(REPLACE(stat_longdesc, ';', ','), ';')
        WITHIN GROUP (ORDER BY sort_order, stat_longdesc, depcode)
      AS csv_line
    FROM cols

    UNION ALL

    -- 5.2 Вторая строка заголовка: depcode
    SELECT
      1 AS ord,
      NULL AS wdate,
      NULL AS xdesc,
      'xcma_longdesc;wdat_date;' ||
      LISTAGG(REPLACE(depcode, ';', ','), ';')
        WITHIN GROUP (ORDER BY sort_order, stat_longdesc, depcode)
      AS csv_line
    FROM cols

    UNION ALL

    -- 5.3 Данные
    SELECT
      2 AS ord,
      r.wdat_date AS wdate,
      r.xcma_longdesc AS xdesc,
      REPLACE(r.xcma_longdesc, ';', ' ') || ';' ||
      TO_CHAR(r.wdat_date, 'YYYY-MM-DD') || ';' ||
      LISTAGG(
        TO_CHAR(NVL(b.amount, 0), 'FM9999999990.00'),
        ';'
      ) WITHIN GROUP (ORDER BY c.sort_order, c.stat_longdesc, c.depcode)
      AS csv_line
    FROM row_keys r
    CROSS JOIN cols c
    LEFT JOIN base b
      ON b.xcma_longdesc = r.xcma_longdesc
     AND b.wdat_date     = r.wdat_date
     AND b.stat_longdesc = c.stat_longdesc
     AND b.depcode       = c.depcode
    GROUP BY r.xcma_longdesc, r.wdat_date
  )
)
ORDER BY ord, wdate, xdesc
