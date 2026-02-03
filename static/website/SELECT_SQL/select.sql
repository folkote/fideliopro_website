select
'reservation id;creation date;arrival;departure;rate amount;nights;shource code;group;block;status;category;rate code;adult number;no of rooms;cancellation date;packages;market;company agent;rates' header
from
dual
union all
select
to_char(yres_id)
|| ';' || to_char(wmlg_time_creation, 'dd.mm.yyyy HH24:MI:SS')
|| ';' || to_char(yres_exparrtime, 'dd.mm.yyyy')
|| ';' || to_char(yres_expdeptime, 'dd.mm.yyyy')
|| ';' || to_char(round(conf_rate))
|| ';' || to_char(nights)
|| ';' || source_shortdesc
|| ';' || ri.group_name
|| ';' || ri.yblh_longdesc
|| ';' || decode(yres_resstatus, 3, 'Inactive', 'Active')
|| ';' || ycat_longdesc
|| ';' || yrch_shortdesc
|| ';' || ydet_adultno
|| ';' || ydet_noofrooms
|| ';' || to_char(ri.ycxl_date, 'dd.mm.yyyy HH24:MI:SS')
|| ';' || to_char((select avg(ypal_value) from ydet,ypal,ypac where
                ypal_included = 1 and ypal_ydet_id = ydet_id
                and ypal_ypac_id = ypac_id and ydet_yres_id = yres_id))
|| ';' || ri.xcma_shortdesc
|| ';' || nvl(nvl(ri.sourcename, ri.travelagent_name), ri.company_name)
|| ';' || aggregate_field('select ydet_finalamount  from ydet where ydet_yres_id =  ' || to_char(yres_id) || ' order by ydet_date asc', '/')
|| ';' || aggregate_field('select ypal_value from ydet,ypal,ypac where ypal_included = 1 and ypal_ydet_id = ydet_id and ypal_ypac_id = ypac_id and ydet_yres_id = ' || to_char(yres_id) || ' order by ydet_date asc', '/')

from
    (SELECT
  YRES.YRES_ID,
  YRES.YRES_EXPARRTIME YRES_EXPARRTIME,
  YRES.YRES_EXPDEPTIME YRES_EXPDEPTIME,
  (YRES.YRES_EXPDEPTIME) - (YRES.YRES_EXPARRTIME) Nights,
  YRES.YRES_RESSTATUS YRES_RESSTATUS,
  (SELECT YDET.YDET_ADULTNO FROM YDET WHERE YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) YDET_ADULTNO,  
  (SELECT YRAS.YRAS_SHORTDESC FROM YRAL,YRAS,YRAC,YDET WHERE YRAL.yral_ydet_id = YDET.ydet_id AND YRAL.yral_yras_id = YRAS.yras_id AND YRAL.yral_yrac_id = YRAC.yrac_id AND YRAC.yrac_ID = 1 AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID AND ROWNUM=1) SOURCE_SHORTDESC,  
  (DECODE(NVL((SELECT YDET.YDET_SHARENUM FROM YDET WHERE YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID),0),0,(SELECT YDET.YDET_NOOFROOMS FROM YDET WHERE YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID),(CASE WHEN (YRES.YRES_HASSHARE=1 AND YRES.YRES_ID=(SELECT MIN(ydet_2.YDET_YRES_ID) FROM YDET,YDET ydet_2 WHERE YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID AND YDET.YDET_SHARENUM=ydet_2.YDET_SHARENUM GROUP BY ydet_2.YDET_SHARENUM)) THEN (SELECT AVG(ydet_2.YDET_NOOFROOMS) FROM YDET,YDET ydet_2 WHERE YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID AND YDET.YDET_SHARENUM=ydet_2.YDET_SHARENUM GROUP BY ydet_2.YDET_SHARENUM) ELSE 0 END))) YDET_NOOFROOMS,
  (SELECT YCAT.YCAT_LONGDESC FROM YCAT,YDET WHERE YCAT.YCAT_ID=YDET.YDET_YCAT_ID AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) YCAT_LONGDESC,
  (SELECT YBLH.YBLH_LONGDESC FROM YBLH,YBLD,YDET WHERE YBLH.YBLH_ID=YBLD.YBLD_YBLH_ID AND YBLD.YBLD_ID=YDET.YDET_YBLD_ID AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) YBLH_LONGDESC,  
  (SELECT getYDetDiscountedAmount(ydet_rateamount,ydet_ratemanual,ydet_ratediff,ydet_ratediscountperc,ydet_nodiscountpackage,ydet_finalAmount)
         -NVL((SELECT SUM(DECODE(YPAL.YPAL_INCLUDED,0,YPAL.YPAL_VALUE,0)) FROM YPAL WHERE YPAL.YPAL_YDET_ID=YDET.YDET_ID),0) 
   FROM YDET WHERE YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) CONF_RATE,
  (select
   sum(ypal.ypal_value)
from
    ydet
    , ypal
    , ypac
where
    ydet_id = ypal_ydet_id and
    ypal_ypac_id = ypac_id
    and ydet_yres_id = yres.yres_id
  ) ADD_ON_PACKAGES,
  NVL((SELECT SUM(YFXC.YFXC_AMOUNT*YFXC.YFXC_QUANTITY) FROM YFXC,YDET WHERE YFXC.YFXC_YDET_ID=YDET.YDET_ID AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID),0) TOTAL_FIX_CHARGES,
  (SELECT YRCH.YRCH_SHORTDESC FROM YRCH,YDET WHERE YRCH.YRCH_ID=YDET.YDET_YRCH_ID AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) YRCH_SHORTDESC,
  (SELECT YGRP.YGRP_NAME FROM YGRP,YDET WHERE YGRP.YGRP_ID=YDET.YDET_YGRP_ID AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) YDET_GROUP_NAME,
  (CASE WHEN (NVL(YRES.YRES_XCMS_ID,0)=0 AND NVL(YRES.YRES_YGRP_ID,0)<>0) THEN (SELECT YGRP.YGRP_NAME FROM YGRP WHERE YGRP.YGRP_ID=YRES.YRES_YGRP_ID) ELSE (SELECT YGRP.YGRP_NAME FROM YGRP,YDET WHERE YGRP.YGRP_ID=YDET.YDET_YGRP_ID AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) END) GROUP_NAME,
  (SELECT v8_rep_name.NAME2 FROM v8_rep_name,YCLN,YDET WHERE v8_rep_name.XCMS_ID=YCLN.YCLN_XCMS_ID AND YCLN.YCLN_YDET_ID=YDET.YDET_ID AND YCLN.YCLN_XCCA_INTERNALCATEGORY=1 AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) COMPANY_NAME,
  (SELECT v8_rep_name.NAME2 FROM v8_rep_name,YCLN,YDET WHERE v8_rep_name.XCMS_ID=YCLN.YCLN_XCMS_ID AND YCLN.YCLN_YDET_ID=YDET.YDET_ID AND YCLN.YCLN_XCCA_INTERNALCATEGORY=2 AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID and rownum = 1) TRAVELAGENT_NAME,
  (SELECT YCXL.YCXL_DATE FROM YCXL WHERE YCXL.YCXL_ID=(SELECT MAX(ycxl_2.YCXL_ID) FROM YCXL ycxl_2 WHERE ycxl_2.YCXL_YRES_ID=YRES.YRES_ID AND ycxl_2.YCXL_CANCELORREINSTATE=1)) YCXL_DATE,
  (SELECT WMLG.WMLG_TIME_CREATION FROM WMLG WHERE WMLG.WMLG_TABLENAME='YRES' AND WMLG.WMLG_TABLE_ID=YRES.YRES_ID) WMLG_TIME_CREATION,
    (SELECT YCAT.YCAT_SHORTDESC FROM YCAT,YDET WHERE YCAT.YCAT_ID=YDET.YDET_YCAT_ID AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) YCAT_SHORTDESC,
  (SELECT XCMA.XCMA_SHORTDESC FROM XCMA,YDET WHERE XCMA.XCMA_ID=YDET.YDET_XCMA_ID AND YDET.YDET_ID=YRES.YRES_CURRENT_YDET_ID) XCMA_SHORTDESC,
   (select trim(trim(xcms_name1 || ' ' || xcms_name2) || ' ' || xcms_name3) from ycln, xcms
    where ycln.ycln_xcca_internalcategory = 3 and ycln_ydet_id = yres.yres_last_ydet_id and rownum = 1
    and ycln_xcms_id = xcms_id) sourcename
FROM
YRES) ri