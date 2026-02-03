select
'Date;Category;RoomsOut;AvailableRooms;Blocks;RoomsSoldIndividual;RoomsSoldGroup;RoomsNondeductedGroup;GrossRoomRevenueDeductedIndividual;GrossRoomRevenueExtrachargeDeductedIndividual;GrossRoomRevenueDeductedGroup;GrossRoomRevenueExtrachargeDeductedGroup;GrossFBRevenueIncludedDeductedIndividual;GrossFBRevenueIncludedDeductedGroup;GrossOtherRevenueIncludedDeductedIndividual;GrossOtherRevenueIncludedDeductedGroup' header
from dual
union all
select
    to_char(wdat_date, 'dd.mm.yyyy')
    || ';' || ycat_shortdesc || ' ' || ycat_longdesc
    || ';' || nvl((select count(distinct YRST_YRMS_ID)
                  from YRST,YRSC, yrms
                  where YRST_FROMTIME<=WDAT_DATE
                    and trunc(YRST_UNTILTIME)>WDAT_DATE
                    and YRST.YRST_YRSC_ID=YRSC_ID
                    and YRSC.YRSC_AFFECTAILABILITY=1
                    and yrst.yrst_yrms_id = yrms_id
                    and yrms_ycat_id = ycat.ycat_id), 0

    )
    || ';' || nvl((select count(yrms_id) from yrms where yrms_validfrom <= wdat.wdat_date
        and yrms_validuntil >= wdat.wdat_date and yrms_ycat_id = ycat.ycat_id), 0)
    || ';' || nvl((select sum(ybld.ybld_actualnoofrooms) from ybld, yblh where ybld_yblh_id = yblh_id
        and nvl(yblh.yblh_inactive, 0) = 0 and ybld.ybld_date = wdat.wdat_date
        and ybld.ybld_ycat_id = ycat.ycat_id), 0)
    || ';' || nvl((select sum(noofrooms) from m_ydet where ydet_date = wdat.wdat_date
        and ydet_ycat_id = ycat.ycat_id and nvl(ydet_ygrp_id, 0) = 0), 0)
    || ';' || nvl((select sum(noofrooms) from m_ydet where ydet_date = wdat.wdat_date
        and ydet_ycat_id = ycat.ycat_id and nvl(ydet_ygrp_id, 0) > 0), 0)
    || ';' || 0
    || ';' || nvl((select sum(zpos_grossunitprice * zpos_quantity) from m_zpos_ypos zpos, zdco, yres, ydet where zpos_postdate = wdat.wdat_date
        and zpos_originated_yres_id = yres_id and yres_last_ydet_id = ydet_id
        and ydet_ycat_id = ycat.ycat_id and zpos_zdco_id = zdco_id and zdco_stats_type = 1
        and zdco_cdt = 1 and nvl(ydet_ygrp_id, 0) = 0), 0)
    || ';' || nvl((select sum(zpos_grossunitprice * zpos_quantity) from m_zpos_ypos zpos, zdco, yres, ydet where zpos_postdate = wdat.wdat_date
        and zpos_originated_yres_id = yres_id and yres_last_ydet_id = ydet_id
        and not exists (select yrch_id from yrch where yrch.yrch_zdco_id = zdco.zdco_id)
        and ydet_ycat_id = ycat.ycat_id and zpos_zdco_id = zdco_id and zdco_stats_type = 1
        and zdco_cdt = 1 and not exists (select ycln_id from ycln where ycln_ydet_id = ydet.ydet_id
                and ycln.ycln_xcca_internalcategory in (1,2))), 0)
    || ';' || nvl((select sum(zpos_grossunitprice * zpos_quantity) from m_zpos_ypos zpos, zdco, yres, ydet where zpos_postdate = wdat.wdat_date
        and zpos_originated_yres_id = yres_id and yres_last_ydet_id = ydet_id
        and ydet_ycat_id = ycat.ycat_id and zpos_zdco_id = zdco_id and zdco_stats_type = 1
        and zdco_cdt = 1 and nvl(ydet_ygrp_id, 0) > 0), 0)
    || ';' || nvl((select sum(zpos_grossunitprice * zpos_quantity) from m_zpos_ypos zpos, zdco, yres, ydet where zpos_postdate = wdat.wdat_date
        and zpos_originated_yres_id = yres_id and yres_last_ydet_id = ydet_id
        and not exists (select yrch_id from yrch where yrch.yrch_zdco_id = zdco.zdco_id)
        and ydet_ycat_id = ycat.ycat_id and zpos_zdco_id = zdco_id and zdco_stats_type = 1
        and zdco_cdt = 1 and nvl(ydet_ygrp_id, 0) > 0), 0)
    || ';' || nvl((select sum(zpos_grossunitprice * zpos_quantity) from m_zpos_ypos zpos, zdco, yres, ydet where zpos_postdate = wdat.wdat_date
        and zpos_originated_yres_id = yres_id and yres_last_ydet_id = ydet_id
        and nvl(zpos.zpos_manualpost, 0) = 0
        and ydet_ycat_id = ycat.ycat_id and zpos_zdco_id = zdco_id and zdco_stats_type = 2
        and zdco_cdt = 1 and nvl(ydet_ygrp_id, 0) = 0), 0)
    || ';' || nvl((select sum(zpos_grossunitprice * zpos_quantity) from zpos, zdco, yres, ydet where zpos_postdate = wdat.wdat_date
        and zpos_originated_yres_id = yres_id and yres_last_ydet_id = ydet_id
        and nvl(zpos.zpos_manualpost, 0) = 0
        and ydet_ycat_id = ycat.ycat_id and zpos_zdco_id = zdco_id and zdco_stats_type = 2
        and zdco_cdt = 1 and nvl(ydet_ygrp_id, 0) > 0), 0)
    || ';' || nvl((select sum(zpos_grossunitprice * zpos_quantity) from m_zpos_ypos zpos, zdco, yres, ydet where zpos_postdate = wdat.wdat_date
        and zpos_originated_yres_id = yres_id and yres_last_ydet_id = ydet_id
        and ydet_ycat_id = ycat.ycat_id and zpos_zdco_id = zdco_id and zdco_stats_type > 2
        and zdco_cdt = 1 and nvl(ydet_ygrp_id, 0) = 0), 0)
    || ';' || nvl((select sum(zpos_grossunitprice * zpos_quantity) from m_zpos_ypos zpos, zdco, yres, ydet where zpos_postdate = wdat.wdat_date
        and zpos_originated_yres_id = yres_id and yres_last_ydet_id = ydet_id
        and nvl(zpos.zpos_manualpost, 0) = 0
        and ydet_ycat_id = ycat.ycat_id and zpos_zdco_id = zdco_id and zdco_stats_type = 2
        and zdco_cdt = 1 and nvl(ydet_ygrp_id, 0) > 0), 0)
from wdat, ycat
where wdat_date in (select ydet_date from ydet)
and nvl(ycat_disabled, 0) = 0