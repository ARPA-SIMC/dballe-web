#include "datagridmodel.h"
#include <dballe/core/var.h>
#include <QDebug>
#include <sstream>

using namespace std;
using namespace dballe;

DataGridModel::DataGridModel(Model& model, QObject *parent) :
    QAbstractTableModel(parent), model(model)
{
    QObject::connect(&model, SIGNAL(data_changed()),
                     this, SLOT(on_model_refreshed()));
}

int DataGridModel::rowCount(const QModelIndex &parent) const
{
    if (parent.isValid()) return 0;
    return model.values().size();
}

int DataGridModel::columnCount(const QModelIndex &parent) const
{
    if (parent.isValid()) return 0;
    return 10;
}

QVariant DataGridModel::data(const QModelIndex &index, int role) const
{
    if (role != Qt::DisplayRole)
        return QVariant();

    if (!index.isValid()) return QVariant();
    if ((unsigned)index.row() >= model.values().size()) return QVariant();
    const Value& val = model.values()[index.row()];
    const Station* sta = model.station(val.ana_id);
    stringstream ss_lev;
    ss_lev << val.level;
    stringstream ss_tr;
    ss_tr << val.trange;
    string varcode = format_code(val.var.code());
    string value = val.var.format();
    char datetime[20];
    snprintf(datetime, 20, "%04d-%02d-%02d %02d:%02d:%02d",
             val.date[0], val.date[1], val.date[2],
             val.date[3], val.date[4], val.date[5]);

    switch (index.column())
    {
    case 0: return QVariant(val.ana_id);
    case 1: return sta ? QVariant(sta->lat) : QVariant();
    case 2: return sta ? QVariant(sta->lon) : QVariant();
    case 3: return QVariant(sta->ident.c_str());
    case 4: return QVariant(val.rep_memo.c_str());
    case 5: return QVariant(ss_lev.str().c_str());
    case 6: return QVariant(ss_tr.str().c_str());
    case 7: return QVariant(datetime);
    case 8: return QVariant(varcode.c_str());
    case 9: return QVariant(value.c_str());
    default: return QVariant();
    }
}

QVariant DataGridModel::headerData(int section, Qt::Orientation orientation, int role) const
{
    if (role != Qt::DisplayRole)
        return QVariant();

    if (orientation != Qt::Horizontal)
        return QVariant();

    switch (section)
    {
    case 0: return QVariant("St.ID");
    case 1: return QVariant("Lat");
    case 2: return QVariant("Lon");
    case 3: return QVariant("Ident");
    case 4: return QVariant("Rep");
    case 5: return QVariant("Level");
    case 6: return QVariant("Trange");
    case 7: return QVariant("Date");
    case 8: return QVariant("Var");
    case 9: return QVariant("Value");
    default: return QVariant();
    }
}

void DataGridModel::on_model_refreshed()
{
    reset();
}
