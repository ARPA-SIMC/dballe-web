#include "tests.h"
#include "provami/model.h"
#include <dballe/types.h>
#include <dballe/core/values.h>
#include <dballe/core/record.h>
#include <QDebug>

using namespace std;
using namespace wreport;
using namespace wreport::tests;
using namespace dballe;
using namespace provami;

namespace {

shared_ptr<DB> populate()
{
    std::shared_ptr<DB> db = DB::connect_test();
    db->reset();

    string stations[] = {
        "lat=45.0, lon=11.0",
        "lat=46.0, lon=12.0",
        "lat=45.0, lon=11.0, ident=foo",
        "lat=45.0, lon=11.0, ident=bar",
    };
    string records[] = {
        "synop",
        "temp",
    };
    Datetime datetimes[] = {
        Datetime(2015, 1, 1, 0, 0, 0),
        Datetime(2015, 2, 1, 0, 0, 0),
    };

    auto tr = db->transaction();
    auto rec = Record::create();
    for (auto s: stations)
        for (auto r: records)
            for (auto d: datetimes)
            {
                rec->clear();
                core::Record::downcast(*rec).set_from_test_string(s);
                rec->set("rep_memo", r);
                rec->set(Level(1, 0));
                rec->set(Trange::instant());
                rec->set(d);
                rec->set(newvar(WR_VAR(0, 12, 101), 280.0));
                DataValues dv(*rec);
                tr->insert_data(dv, true, true);
            }
    tr->commit();

    return db;
}

class Tests : public TestCase
{
    using TestCase::TestCase;

    void register_tests() override
    {
        add_method("filter", []() {
            qDebug() << "start";
            Model model;
            model.set_db(populate(), "test");
            model.activate_next_filter();

            qDebug() << "have db";

            model.test_wait_for_refresh();

            qDebug() << "populated";

            wassert(actual(model.summary_datetime_min()) == Datetime(2015, 1, 1));
            wassert(actual(model.summary_datetime_max()) == Datetime(2015, 2, 1));
            wassert(actual(model.summary_count()) == 16);
            wassert(actual(model.stations().size()) == 8);
            wassert(actual(model.values().size()) == 16);

            qDebug() << "filter";

            model.select_report("temp");
            model.activate_next_filter(true);
            model.test_wait_for_refresh();

            wassert(actual(model.summary_datetime_min()) == Datetime(2015, 1, 1));
            wassert(actual(model.summary_datetime_max()) == Datetime(2015, 2, 1));
            wassert(actual(model.summary_count()) == 8);
            wassert(actual(model.values().size()) == 8);
            wassert(actual(model.stations().size()) == 8);
        });
    }
} tests("model");

}
