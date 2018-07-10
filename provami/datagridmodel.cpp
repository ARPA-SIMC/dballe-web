#include "datagridmodel.h"
#include <QDebug>
#include <sstream>

using namespace std;
using namespace dballe;
using namespace wreport;

namespace provami {

DataGridModel::DataGridModel(Model& model, QObject *parent) :
    QAbstractTableModel(parent), model(model)
{
    QObject::connect(&model, SIGNAL(begin_data_changed()),
                     this, SLOT(on_model_begin_refresh()));
    QObject::connect(&model, SIGNAL(end_data_changed()),
                     this, SLOT(on_model_end_refresh()));
}

DataGridModel::ColumnType DataGridModel::resolveColumnType(int column) const
{
    switch (column)
    {
    case 0: return CT_STATION;
    case 1: return CT_NETWORK;
    case 2: return CT_LEVEL;
    case 3: return CT_TRANGE;
    case 4: return CT_DATETIME;
    case 5: return CT_VARCODE;
    case 6: return CT_VALUE;
    default: return CT_INVALID;
    }
}

int DataGridModel::rowCount(const QModelIndex &parent) const
{
    if (parent.isValid()) return 0;
    return model.values().size();
}

int DataGridModel::columnCount(const QModelIndex &parent) const
{
    if (parent.isValid()) return 0;
    return 7;
}

QVariant DataGridModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid()) return QVariant();
    if ((unsigned)index.row() >= model.values().size()) return QVariant();
    ColumnType ctype = resolveColumnType(index.column());
    if (ctype == CT_INVALID) return QVariant();

    switch (role)
    {
    case Qt::DisplayRole:
    {
        const Value& val = model.values()[index.row()];
        switch (ctype)
        {
        case CT_STATION: return QVariant(val.ana_id);
        case CT_NETWORK: return QVariant(val.rep_memo.c_str());
        case CT_LEVEL:
        {
            stringstream ss_lev;
            ss_lev << val.level;
            return QVariant(ss_lev.str().c_str());
        }
        case CT_TRANGE:
        {
            stringstream ss_tr;
            ss_tr << val.trange;
            return QVariant(ss_tr.str().c_str());
        }
        case CT_DATETIME:
        {
            char datetime[20];
            snprintf(datetime, 20, "%04d-%02d-%02d %02d:%02d:%02d",
                     val.date.year, val.date.month, val.date.day,
                     val.date.hour, val.date.minute, val.date.second);
            return QVariant(datetime);
        }
        case CT_VARCODE: return QVariant(varcode_format(val.var.code()).c_str());
        case CT_VALUE: return QVariant(val.var.format().c_str());
        default: return QVariant();
        }
        break;
    }
    case Qt::ToolTipRole:
    case Qt::StatusTipRole:
    {
        const Value& val = model.values()[index.row()];
        switch (ctype)
        {
        case CT_STATION:
        {
            const Station* sta = model.station(val.ana_id);
            if (sta->ident.empty())
            {
                return QString("Fixed station, lat %1 lon %2").arg(sta->lat).arg(sta->lon);
            } else {
                return QString("Mobile station %1 at lat %2 lon %3")
                        .arg(sta->ident.c_str()).arg(sta->lat).arg(sta->lon);
            }
        }
        case CT_NETWORK: return QString("Station network: %1").arg(val.rep_memo.c_str());
        case CT_LEVEL: return QVariant(val.level.describe().c_str());
        case CT_TRANGE: return QVariant(val.trange.describe().c_str());
        case CT_DATETIME:
        {
            char datetime[20];
            snprintf(datetime, 20, "%04d-%02d-%02d %02d:%02d:%02d",
                     val.date.year, val.date.month, val.date.day,
                     val.date.hour, val.date.minute, val.date.second);
            return QVariant(datetime);
        }
        case CT_VARCODE:
        {
            return QString(val.var.info()->desc);
        }
        case CT_VALUE:
        {
            return QString("%1: %2 %3").arg(
                        QString(val.var.info()->desc),
                        QString(val.var.format().c_str()),
                        QString(val.var.info()->unit));
        }
        default: return QVariant();
        }
        break;
    }
    }
    return QVariant();
}

QVariant DataGridModel::headerData(int section, Qt::Orientation orientation, int role) const
{
    if (role != Qt::DisplayRole)
        return QVariant();

    if (orientation != Qt::Horizontal)
        return QVariant();

    switch (resolveColumnType(section))
    {
    case CT_STATION: return QVariant("St.ID");
    case CT_NETWORK: return QVariant("Rep");
    case CT_LEVEL: return QVariant("Level");
    case CT_TRANGE: return QVariant("Trange");
    case CT_DATETIME: return QVariant("Date");
    case CT_VARCODE: return QVariant("Var");
    case CT_VALUE: return QVariant("Value");
    default: return QVariant();
    }
}

Qt::ItemFlags DataGridModel::flags(const QModelIndex &index) const
{
    if (!index.isValid()) return Qt::NoItemFlags;
    if ((unsigned)index.row() >= model.values().size()) return Qt::NoItemFlags;

    Qt::ItemFlags res = Qt::ItemIsEnabled | Qt::ItemIsSelectable;
    if (resolveColumnType(index.column()) == CT_VALUE)
        res |= Qt::ItemIsEditable;
    return res;
}

bool DataGridModel::setData(const QModelIndex &index, const QVariant &value, int role)
{
    if (!index.isValid()) return false;
    if ((unsigned)index.row() >= model.values().size()) return false;
    if (resolveColumnType(index.column()) != CT_VALUE) return false;

    // Skip changes on empty strings
    QString str_val = value.toString();
    if (str_val.isEmpty()) return false;
    QByteArray utf8_val = str_val.toUtf8();

    // Access the value we need to change
    Value& val = model.values()[index.row()];
    wreport::Var new_var(val.var);
    try {
        new_var.setf(utf8_val.constData());
    } catch (std::exception& e) {
        qDebug() << "Cannot set value:" << e.what();
        return false;
    }

    try {
        model.update(val, new_var);
    } catch (std::exception& e) {
        qDebug() << "Cannot save value in the database:" << e.what();
        return false;
    }

    emit dataChanged(index, index);

    return true;
}

const Value *DataGridModel::valueAt(const QModelIndex &index) const
{
    if (!index.isValid()) return NULL;
    if ((unsigned)index.row() >= model.values().size()) return NULL;
    const Value& val = model.values()[index.row()];
    return &val;
}

void DataGridModel::on_model_begin_refresh()
{
    beginResetModel();
}

void DataGridModel::on_model_end_refresh()
{
    endResetModel();
}

}
