#include "provami/model.h"
#include <memory>
#include <dballe/db/db.h>
#include <dballe/core/values.h>
#include <set>
#include <algorithm>
#include <QDebug>
#include <QEventLoop>

using namespace std;
using namespace dballe;

namespace provami {

Model::Model()
    : db(0), active_filter(Query::create()), next_filter(Query::create()),
      reports(*this), levels(*this), tranges(*this), varcodes(*this), idents(*this)
{
}

Model::~Model()
{
    delete global_summary;
    delete active_summary;
}

static const dballe::Datetime missing_datetime;

const Datetime &Model::summary_datetime_min() const
{
    if (!active_summary) return missing_datetime;
    return active_summary->datetime_min();
}

const Datetime &Model::summary_datetime_max() const
{
    if (!active_summary) return missing_datetime;
    return active_summary->datetime_max();
}

unsigned Model::summary_count() const
{
    if (!active_summary) return dballe::MISSING_INT;
    return active_summary->data_count();
}

const std::map<int, Station> &Model::stations() const
{
    return cache_stations;
}

const std::set<int> &Model::selected_stations() const
{
    return _selected_stations;
}

const Station *Model::station(int id) const
{
    std::map<int, Station>::const_iterator i = cache_stations.find(id);
    if (i == cache_stations.end())
        return 0;
    return &(i->second);
}

const std::vector<Value> &Model::values() const
{
    return cache_values;
}

std::vector<Value> &Model::values()
{
    return cache_values;
}

void Model::update(Value &val, const wreport::Var &new_val)
{
    DataValues vals;
    vals.info.id = val.ana_id;
    vals.info.report = val.rep_memo;
    vals.info.level = val.level;
    vals.info.trange = val.trange;
    vals.info.datetime = val.date;
    vals.values.set(new_val);
    db->insert_data(vals, true, false);
    val.var = new_val;
}

void Model::update(StationValue &val, const wreport::Var &new_val)
{
    StationValues vals;
    vals.info.id = val.ana_id;
    vals.info.report = val.rep_memo;
    vals.values.set(new_val);
    db->insert_station_data(vals, true, false);
    val.var = new_val;
}

void Model::update(int var_id, wreport::Varcode var_related, const wreport::Var &new_val)
{
    Values values;
    values.set(new_val);
    db->attr_insert_data(var_id, values);
}

void Model::remove(const Value &val)
{
    emit begin_data_changed();
    auto change = Query::create();
    core::Query::downcast(*change).ana_id = val.ana_id;
    core::Query::downcast(*change).rep_memo = val.rep_memo;
    change->set_level(val.level);
    change->set_trange(val.trange);
    change->set_datetimerange(DatetimeRange(val.date, val.date));
    core::Query::downcast(*change).varcodes.clear();
    core::Query::downcast(*change).varcodes.insert(val.var.code());
    db->remove(*change);
    vector<Value>::iterator i = std::find(cache_values.begin(), cache_values.end(), val);
    if (i != cache_values.end())
    {
        cache_values.erase(i);
    }
    emit end_data_changed();
}

void Model::set_initial_filter(const Query& rec)
{
    active_filter = rec.clone();
    next_filter = rec.clone();
}

void Model::dballe_connect(const std::string &dballe_url)
{
    if (db)
        db.reset();

    m_dballe_url = dballe_url;

    db = DB::connect_from_url(dballe_url.c_str());

    //refresh();
}

void Model::set_db(std::shared_ptr<DB> db, const std::string& url)
{
    m_dballe_url = url;
    this->db = db;

    //refresh();
}

void Model::test_wait_for_refresh()
{
/*
    if (pending_query_data)
        pending_query_data->future_watcher.waitForFinished();
    if (pending_query_summary)
        pending_query_summary->future_watcher.waitForFinished();

    QEventLoop loop;
    loop.processEvents();
 */
}

std::shared_ptr<dballe::db::Transaction> Model::get_refresh_transaction()
{
    if (!refresh_transaction.expired())
        return refresh_transaction.lock();
    auto res = db->transaction(); // TODO: make it read only
    refresh_transaction = res;
    return res;
}

void Model::refresh(bool accurate)
{
    refresh_data();
    refresh_summary(accurate);
}

void Model::refresh_data()
{
    emit progress("data", "Loading data...");
    auto tr = get_refresh_transaction();
    auto query = active_filter->clone();
    core::Query::downcast(*query).limit = limit;
    on_have_new_data(tr->query_data(*query));
}

void Model::on_have_new_data(std::unique_ptr<db::CursorData> cur)
{
    emit progress("data", "Processing data...");

    emit begin_data_changed();
    // Query data for the currently active filter
    cache_values.clear();
    while (cur->next())
    {
        cache_values.push_back(Value(*cur));
    }
    emit end_data_changed();

    emit progress("data");
}

void Model::refresh_summary(bool accurate)
{
    using namespace dballe::db::summary;

    emit progress("summary", "Loading summary...");

    delete active_summary;
    active_summary = nullptr;

    unique_ptr<Query> query;

    db::summary::Support supported = UNSUPPORTED;
    if (!global_summary)
    {
        query = Query::create();
        core::Query::downcast(*query).query = "details";
    } else {
        supported = global_summary->supports(*active_filter);
//        Matcher matcher(*active_filter, cache_stations);
//        supported = summaries.query(*active_filter, accurate, [&](const Entry& entry) {
//            return matcher.match(entry);
//        });
        query = active_filter->clone();
        if (accurate)
            core::Query::downcast(*query).query = "details";
    }


    if (supported == UNSUPPORTED || (supported == OVERESTIMATED && accurate))
    {
        // The best summary that we have do not support what we need: hit the database
        emit progress("summary", "Loading summary from db...");
        auto tr = get_refresh_transaction();
        on_have_new_summary(tr->query_summary(*query), *query);
    }
    else
    {
        // Recompute the available choices
        qDebug() << "No need to hit the database, summary collation started";

        Matcher matcher(*query, cache_stations);
        if (active_summary)
        {
            delete active_summary;
            active_summary = nullptr;
        }
        active_summary = new db::Summary(*query);
        filter_top_summary(matcher, *active_summary);

        process_summary();
        emit progress("summary");
        emit active_filter_changed();
    }
}

void Model::on_have_new_summary(std::unique_ptr<db::CursorSummary> cur, const dballe::Query& query)
{
    emit progress("summary", "Processing summary...");
    qDebug() << "Refresh summary results arrived";

    bool do_global_summary = false;
    if (!global_summary)
    {
        do_global_summary = true;
        auto query = dballe::Query::create();
        global_summary = new db::Summary(*query);
    }

    // Get the result out of the pending action
    if (active_summary)
    {
        delete active_summary;
        active_summary = nullptr;
    }
    active_summary = new db::Summary(query);

    if (do_global_summary)
        cache_stations.clear();

    highlight.reset();

    while (cur->next())
    {
        active_summary->add_summary(*cur);

        if (do_global_summary)
        {
            int ana_id = cur->get_station_id();
            if (cache_stations.find(ana_id) == cache_stations.end())
                cache_stations.insert(make_pair(ana_id, Station(*cur)));
            global_summary->add_summary(*cur);
        }
    }

    // Recompute the available choices
    qDebug() << "Summary collation started";
    process_summary();
    emit progress("summary");
    emit active_filter_changed();
}

void Model::activate_next_filter(bool accurate)
{
    active_filter = next_filter->clone();
    refresh(accurate);
}

void Model::filter_top_summary(const Matcher &matcher, db::Summary &out) const
{
    global_summary->iterate([&](const db::summary::Entry& entry) {
        if (matcher.match(entry))
            out.add_entry(entry);
        return true;
    });
}

void Model::mark_hidden_stations(const db::Summary &summary)
{
    for (auto& s: cache_stations)
        s.second.hidden = summary.all_stations.find(s.first) == summary.all_stations.end();
}

void Model::process_summary()
{
    qDebug() << "process_summary";
    next_filter->print(stderr);

    // We need at least a master summary to process
    if (!global_summary) return;

    Matcher matcher(*next_filter, cache_stations);

    // Filter the toplevel summary using next_filter,
    // to create a summary of what would appear in the next refresh
    db::Summary next_summary(*next_filter);
    filter_top_summary(matcher, next_summary);

    // Mark disappeared stations as hidden
    set<string> all_idents;
    if (matcher.has_flt_station)
    {
        // Build a version of the current filter without station information
        auto subrec = next_filter->clone();
        core::Query::downcast(*subrec).ana_id = MISSING_INT;
        core::Query::downcast(*subrec).mobile = MISSING_INT;
        core::Query::downcast(*subrec).ident.clear();
        subrec->set_latrange(LatRange());
        subrec->set_lonrange(LonRange());

        // Filter the toplevel summary using next_filter minus station information
        db::Summary sub(*subrec);
        {
            Matcher submatcher(*subrec, cache_stations);
            filter_top_summary(submatcher, sub);
        }

        // Mark all stations not present in sub as hidden
        mark_hidden_stations(sub);

        // Harvest all idents from the station present in sub to create a filtered ident selection
        for (const auto& si : sub.all_stations)
            if (!si.second.ident.is_missing())
                all_idents.insert(si.second.ident);

        // Mark all stations selected by next_filter as selected
        _selected_stations.clear();
        for (const auto& si : next_summary.all_stations)
            _selected_stations.insert(si.first);
    } else {
        // If we have no station filter, we can hide all stations
        // that would give no data if the current next_filter were
        // activated
        mark_hidden_stations(next_summary);

        // Harvest all idents from the same set of stations, to create a filtered ident selection
        for (const auto& si : next_summary.all_stations)
            if (!si.second.ident.is_missing())
                all_idents.insert(si.second.ident);

        // No station is currently selected, so clear the list
        _selected_stations.clear();
    }
    idents.set_items(all_idents);

    if (matcher.has_flt_rep_memo)
    {
        auto subrec = next_filter->clone();
        core::Query::downcast(*subrec).rep_memo.clear();
        Matcher submatcher(*subrec, cache_stations);
        db::Summary sub(*subrec);
        filter_top_summary(submatcher, sub);
        reports.set_items(sub.all_reports);
    }
    else
        reports.set_items(next_summary.all_reports);

    if (matcher.has_flt_level)
    {
        auto subrec = next_filter->clone();
        subrec->set_level(Level());
        Matcher submatcher(*subrec, cache_stations);
        db::Summary sub(*subrec);
        filter_top_summary(submatcher, sub);
        levels.set_items(sub.all_levels);
    } else
        levels.set_items(next_summary.all_levels);

    if (matcher.has_flt_trange)
    {
        auto subrec = next_filter->clone();
        subrec->set_trange(Trange());
        Matcher submatcher(*subrec, cache_stations);
        db::Summary sub(*subrec);
        filter_top_summary(submatcher, sub);
        tranges.set_items(sub.all_tranges);
    } else
        tranges.set_items(next_summary.all_tranges);

    if (matcher.has_flt_varcode)
    {
        auto subrec = next_filter->clone();;
        core::Query::downcast(*subrec).varcodes.clear();
        Matcher submatcher(*subrec, cache_stations);
        db::Summary sub(*subrec);
        filter_top_summary(submatcher, sub);
        varcodes.set_items(sub.all_varcodes);
    } else
        varcodes.set_items(next_summary.all_varcodes);

    emit next_filter_changed();
}

void Model::select_report(const string &val)
{
    core::Query::downcast(*next_filter).rep_memo = val;
    process_summary();
}

void Model::select_level(const Level &val)
{
    next_filter->set_level(val);
    process_summary();
}

void Model::select_trange(const Trange &val)
{
    next_filter->set_trange(val);
    process_summary();
}

void Model::select_varcode(wreport::Varcode val)
{
    core::Query::downcast(*next_filter).varcodes.clear();
    core::Query::downcast(*next_filter).varcodes.insert(val);
    process_summary();
}

void Model::select_datemin(const dballe::Datetime& val)
{
    DatetimeRange dtr = next_filter->get_datetimerange();
    if (dtr.min == val) return;
    dtr.min = val;
    next_filter->set_datetimerange(dtr);
    process_summary();
}

void Model::select_datemax(const dballe::Datetime& val)
{
    DatetimeRange dtr = next_filter->get_datetimerange();
    if (dtr.max == val) return;
    dtr.max = val;
    next_filter->set_datetimerange(dtr);
    process_summary();
}

void Model::select_station_id(int id)
{
    next_filter->set_latrange(LatRange());
    next_filter->set_lonrange(LonRange());
    core::Query::downcast(*next_filter).ident.clear();
    core::Query::downcast(*next_filter).ana_id = id;
    process_summary();
}

void Model::select_station_bounds(double latmin, double latmax, double lonmin, double lonmax)
{
    if (latmin < -90) latmin = -90;
    if (latmax > 90) latmax = 90;
    if (lonmin < -180) lonmin = -180;
    if (lonmax > 180) lonmax = 180;

    next_filter->set_latrange(LatRange(latmin, latmax));
    next_filter->set_lonrange(LonRange(lonmin, lonmax));
    core::Query::downcast(*next_filter).ana_id = MISSING_INT;
    process_summary();
}

void Model::select_ident(const string &val)
{
    core::Query::downcast(*next_filter).ident = val;
    core::Query::downcast(*next_filter).ana_id = MISSING_INT;
    process_summary();
}

void Model::unselect_report()
{
    core::Query::downcast(*next_filter).rep_memo.clear();
    process_summary();
}

void Model::unselect_level()
{
    next_filter->set_level(Level());
    process_summary();
}

void Model::unselect_trange()
{
    next_filter->set_trange(Trange());
    process_summary();
}

void Model::unselect_varcode()
{
    core::Query::downcast(*next_filter).varcodes.clear();
    process_summary();
}

void Model::unselect_datemin()
{
    DatetimeRange dtr = next_filter->get_datetimerange();
    if (dtr.min.is_missing()) return;
    dtr.min = Datetime();
    next_filter->set_datetimerange(dtr);
    process_summary();
}

void Model::unselect_datemax()
{
    DatetimeRange dtr = next_filter->get_datetimerange();
    if (dtr.max.is_missing()) return;
    dtr.max = Datetime();
    next_filter->set_datetimerange(dtr);
    process_summary();
}

void Model::set_filter(const Query& new_filter)
{
    next_filter = new_filter.clone();
    process_summary();}

void Model::unselect_station()
{
    next_filter->set_latrange(LatRange());
    next_filter->set_lonrange(LonRange());
    core::Query::downcast(*next_filter).ident.clear();
    core::Query::downcast(*next_filter).ana_id = MISSING_INT;
    process_summary();
}

void Model::unselect_ident()
{
    core::Query::downcast(*next_filter).ident.clear();
    process_summary();
}


ModelAction::ModelAction(Model &model, QObject *parent)
    : QAction(parent), model(model)
{
    connect(this, SIGNAL(triggered()), this, SLOT(on_trigger()));
}

}
