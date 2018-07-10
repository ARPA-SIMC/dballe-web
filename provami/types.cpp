#include "provami/types.h"
#include <dballe/db/db.h>
#include <dballe/db/summary.h>
#include <QDebug>

using namespace dballe;
using namespace std;

namespace provami {

Station::Station(const dballe::db::CursorStation& cur)
{
    id = cur.get_station_id();
    lat = cur.get_lat();
    lon = cur.get_lon();
    ident = cur.get_ident("");
}

Station::Station(const dballe::db::CursorSummary& cur)
{
    id = cur.get_station_id();
    lat = cur.get_lat();
    lon = cur.get_lon();
    ident = cur.get_ident("");
}


BaseValue::BaseValue(const db::CursorValue& cur)
    : var(cur.get_var())
{
    ana_id = cur.get_station_id();
    rep_memo = cur.get_rep_memo();
    value_id = cur.attr_reference_id();
}

StationValue::StationValue(const dballe::db::CursorStationData& cur)
    : BaseValue(cur)
{
}

Value::Value(const dballe::db::CursorData& cur)
    : BaseValue(cur)
{
    level = cur.get_level();
    trange = cur.get_trange();
    date = cur.get_datetime();
}

Matcher::Matcher(const dballe::Query& query_gen, const std::map<int, Station> &all_stations)
{
    const core::Query& query = core::Query::downcast(query_gen);

    // Scan the filter building a todo list of things to match

    // If there is any filtering on the station, build a whitelist of matching stations
    bool has_flt_ident = !query.ident.is_missing();
    bool has_flt_area = !query.get_latrange().is_missing() || !query.get_lonrange().is_missing();
    bool has_flt_station_id = query.ana_id != MISSING_INT;
    if (has_flt_ident || has_flt_area || has_flt_station_id)
    {
        int flt_station_id = query.ana_id;
        LatRange flt_area_latrange = query.get_latrange();
        LonRange flt_area_lonrange = query.get_lonrange();
        has_flt_station = true;
        for (auto s: all_stations)
        {
            const Station& station = s.second;
            if (has_flt_station_id && station.id != flt_station_id)
                continue;

            if (has_flt_area)
            {
                if (!flt_area_latrange.contains(station.lat) ||
                    !flt_area_lonrange.contains(station.lon))
                    continue;
            }
            if (has_flt_ident && query.ident != station.ident)
                continue;

            wanted_stations.insert(station.id);
        }
    }

    has_flt_rep_memo = !query.rep_memo.empty();
    wanted_rep_memo = query.rep_memo;

    has_flt_level = !query.level.is_missing();
    wanted_level = query.level;

    has_flt_trange = !query.trange.is_missing();
    wanted_trange = query.trange;

    has_flt_varcode = !query.varcodes.empty();
    wanted_varcode = has_flt_varcode ? *query.varcodes.begin() : 0;

    wanted_dtrange = query.get_datetimerange();
}

bool Matcher::match(const dballe::db::summary::Entry& entry) const
{
    if (has_flt_station && wanted_stations.find(entry.station.id) == wanted_stations.end())
        return false;

    if (has_flt_rep_memo && wanted_rep_memo != entry.station.report)
        return false;

    if (has_flt_level && wanted_level != entry.level)
        return false;

    if (has_flt_trange && wanted_trange != entry.trange)
        return false;

    if (has_flt_varcode && wanted_varcode != entry.varcode)
        return false;

    if (!wanted_dtrange.contains(entry.dtrange))
        return false;

    return true;
}

}
