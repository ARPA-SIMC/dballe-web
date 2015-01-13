#include "model.h"
#include <memory>
#include <dballe/core/record.h>
#include <dballe/db/db.h>
#include <stdio.h>

using namespace std;

Model::Model()
    : db(0)
{
}

Model::~Model()
{
    if (db) delete db;
}

const std::map<int, Station> &Model::stations() const
{
    return cache_stations;
}

const std::map<SummaryKey, SummaryValue> &Model::summary() const
{
    return cache_summary;
}

const std::vector<Value> &Model::values() const
{
    return cache_values;
}

void Model::dballe_connect(const std::string &dballe_url)
{
    using namespace dballe;

    if (db)
    {
        delete db;
        db = 0;
    }

    auto_ptr<DB> new_db = DB::connect_from_url(dballe_url.c_str());
    db = new_db.release();
    refresh();
}

void Model::refresh()
{
    using namespace dballe;

    fprintf(stderr, "Refresh summary started\n");
    cache_stations.clear();
    cache_summary.clear();
    cache_values.clear();

    Record query;
    auto_ptr<db::Cursor> cur = this->db->query_summary(query);
    while (cur->next())
    {
        int ana_id = cur->get_station_id();
        if (cache_stations.find(ana_id) == cache_stations.end())
            cache_stations.insert(make_pair(ana_id, Station(*cur)));

        cache_summary.insert(make_pair(SummaryKey(*cur), SummaryValue(*cur)));
    }

    fprintf(stderr, "Refresh data started\n");
    query.set("limit", 100);
    cur = this->db->query_data(query);
    while (cur->next())
    {
        cache_values.push_back(Value(*cur));
    }

    fprintf(stderr, "Notifying refresh done\n");

    emit refreshed();

    fprintf(stderr, "Refresh done\n");
}

Station::Station(const dballe::db::Cursor &cur)
{
    using namespace dballe;

    lat = cur.get_lat();
    lon = cur.get_lon();
    ident = cur.get_ident("");
}


bool SummaryKey::operator <(const SummaryKey &sk) const
{
    if (ana_id < sk.ana_id) return true;
    if (ana_id > sk.ana_id) return false;
    if (rep_memo < sk.rep_memo) return true;
    if (rep_memo > sk.rep_memo) return false;
    if (int cmp = level.compare(sk.level)) return cmp < 0;
    if (int cmp = trange.compare(sk.trange)) return cmp < 0;
    return var < sk.var;
}

SummaryKey::SummaryKey(const dballe::db::Cursor &cur)
{
    using namespace dballe;

    ana_id = cur.get_station_id();
    rep_memo = cur.get_rep_memo("");
    level = cur.get_level();
    trange = cur.get_trange();
    var = cur.get_varcode();
}


SummaryValue::SummaryValue(const dballe::db::Cursor &cur)
{

}


Value::Value(const dballe::db::Cursor &cur)
    : var(cur.get_var())
{
    using namespace dballe;

    ana_id = cur.get_station_id();
    rep_memo = cur.get_rep_memo("");
    level = cur.get_level();
    trange = cur.get_trange();
    cur.get_datetime(date);
}
