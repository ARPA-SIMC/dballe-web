#ifndef PROVAMI_TYPES_H
#define PROVAMI_TYPES_H

#include <wreport/var.h>
#include <dballe/types.h>
#include <set>
#include <map>

namespace dballe {
struct Query;
namespace db {
class CursorStation;
class CursorSummary;
class CursorValue;
class CursorStationData;
class CursorData;
namespace summary {
class Entry;
}
}
}

namespace provami {

struct Station
{
    int id;
    double lat;
    double lon;
    std::string ident;
    bool hidden = false;

protected:
    Station(const dballe::db::CursorStation& cur);
    Station(const dballe::db::CursorSummary& cur);

    friend class Model;
};

struct BaseValue
{
    int ana_id;
    int value_id;
    std::string rep_memo;
    wreport::Var var;

    bool operator==(const BaseValue& val) const
    {
        if (ana_id != val.ana_id) return false;
        if (value_id != val.value_id) return false;
        if (var.code() != val.var.code()) return false;
        if (rep_memo != val.rep_memo) return false;
        return true;
    }
protected:
    BaseValue(const dballe::db::CursorValue& cur);
};

struct StationValue : public BaseValue
{
    StationValue(const dballe::db::CursorStationData& cur);
};

struct Value : public BaseValue
{
    dballe::Level level;
    dballe::Trange trange;
    dballe::Datetime date;

    bool operator==(const Value& val) const
    {
        if (!BaseValue::operator==(val)) return false;
        if (level != val.level) return false;
        if (trange != val.trange) return false;
        if (date != val.date) return false;
        return true;
    }

protected:
    Value(const dballe::db::CursorData& cur);

    friend class Model;
};

struct Matcher
{
    bool has_flt_station = false;
    std::set<int> wanted_stations;
    bool has_flt_rep_memo = false;
    std::string wanted_rep_memo;
    bool has_flt_level = false;
    dballe::Level wanted_level;
    bool has_flt_trange = false;
    dballe::Trange wanted_trange;
    bool has_flt_varcode = false;
    wreport::Varcode wanted_varcode;
    dballe::DatetimeRange wanted_dtrange;

    Matcher(const dballe::Query& query, const std::map<int, Station>& all_stations);

    bool match(const dballe::db::summary::Entry& entry) const;
};

}

#endif // TYPES_H
