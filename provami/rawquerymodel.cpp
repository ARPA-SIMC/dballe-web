#include "provami/rawquerymodel.h"
#include <dballe/core/record.h>
#include <QDebug>

using namespace dballe;

namespace provami {

RawQueryModel::RawQueryModel(Model& model, QObject *parent) :
    QAbstractTableModel(parent), model(model)
{
    QObject::connect(&model, SIGNAL(next_filter_changed()), this, SLOT(next_filter_changed()));
}

RawQueryModel::ColumnType RawQueryModel::resolveColumnType(int column) const
{
    switch (column)
    {
    case 0: return CT_KEY;
    case 1: return CT_VALUE;
    default: return CT_INVALID;
    }
}

int RawQueryModel::rowCount(const QModelIndex &parent) const
{
    if (parent.isValid()) return 0;
    return values.size();
}

int RawQueryModel::columnCount(const QModelIndex &parent) const
{
    if (parent.isValid()) return 0;
    return 2;
}

static wreport::Varinfo varinfo_by_name(const std::string& name)
{
    dba_keyword k = Record::keyword_byname_len(name.data(), name.size());
    if (k != DBA_KEY_ERROR)
        return Record::keyword_info(k);
    else
        return varinfo(resolve_varcode_safe(name));
}

QVariant RawQueryModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid()) return QVariant();
    if ((unsigned)index.row() >= values.size()) return QVariant();
    ColumnType ctype = resolveColumnType(index.column());
    if (ctype == CT_INVALID) return QVariant();

    switch (role)
    {
    case Qt::DisplayRole:
    {
        const rawquery::Item& item = values[index.row()];
        switch (ctype)
        {
        case CT_KEY: return QVariant(item.key.c_str());
        case CT_VALUE: return QVariant(item.val.c_str());
        default: return QVariant();
        }
        break;
    }
    case Qt::ToolTipRole:
    case Qt::StatusTipRole:
    {
        const rawquery::Item& item = values[index.row()];
        switch (ctype)
        {
        case CT_KEY:
        {
            if (item.key.empty()) return QVariant();
            try {
                wreport::Varinfo info = varinfo_by_name(item.key);
                return QString(info->desc);
            } catch (std::exception& e) {
                return QVariant(e.what());
            }
        }
        default: return QVariant();
        }
        break;
    }
    }
    return QVariant();
}

QVariant RawQueryModel::headerData(int section, Qt::Orientation orientation, int role) const
{
    if (role != Qt::DisplayRole)
        return QVariant();

    if (orientation != Qt::Horizontal)
        return QVariant();

    switch (resolveColumnType(section))
    {
    case CT_KEY: return QVariant("Key");
    case CT_VALUE: return QVariant("Value");
    default: return QVariant();
    }
}

Qt::ItemFlags RawQueryModel::flags(const QModelIndex &index) const
{
    if (!index.isValid()) return Qt::NoItemFlags;
    if ((unsigned)index.row() >= values.size()) return Qt::NoItemFlags;
    return Qt::ItemIsEnabled | Qt::ItemIsSelectable | Qt::ItemIsEditable;
}

bool RawQueryModel::setData(const QModelIndex &index, const QVariant &value, int role)
{
    if (!index.isValid()) return false;
    if ((unsigned)index.row() >= values.size()) return false;
    ColumnType ctype = resolveColumnType(index.column());
    if (ctype == CT_INVALID) return false;

    // Update values
    switch (ctype)
    {
    case CT_KEY: values[index.row()].key = value.toString().toStdString(); break;
    case CT_VALUE: values[index.row()].val = value.toString().toStdString(); break;
    }

    model.set_filter(build_record());

    return true;
}

const rawquery::Item* RawQueryModel::valueAt(const QModelIndex &index) const
{
    if (!index.isValid()) return NULL;
    if ((unsigned)index.row() >= values.size()) return NULL;
    const rawquery::Item& item = values[index.row()];
    return &item;
}

static std::vector<rawquery::Item> record_to_items(const dballe::Record& rec)
{
    std::vector<rawquery::Item> new_items;

    for (int k = 0; k < (int)DBA_KEY_COUNT; ++k)
        if (auto var = rec.key_peek((dba_keyword)k))
        {
            if (!var->isset()) continue;
            new_items.emplace_back(rawquery::Item{ Record::keyword_name((dba_keyword)k), var->format("") });
        }
    for (auto var: rec.vars())
    {
        if (!var->isset()) continue;
        new_items.emplace_back(rawquery::Item{ wreport::varcode_format(var->code()), var->format("") });
    }

    return new_items;
}

void RawQueryModel::next_filter_changed()
{
    // Rebuild filter
    std::vector<rawquery::Item> new_items = record_to_items(model.next_filter);

    // Preserve the last row if partially edited, or add a new one
    if (!values.empty() && (values.back().key.empty() || values.back().val.empty()))
        new_items.emplace_back(values.back());
    else
        new_items.emplace_back();

    beginResetModel();
    values = new_items;
    endResetModel();
}

Record RawQueryModel::build_record() const
{
    Record new_rec;
    for (const auto& item: values)
    {
        if (item.key.empty() || item.val.empty()) continue;
        try {
            new_rec.set_from_string(item.key.c_str(), item.val.c_str());
        } catch (std::exception) {
            continue;
        }
    }
    return new_rec;
}

static bool is_shell_safe(char c)
{
    if (isalnum(c)) return true;
    switch (c)
    {
    case '@':
    case '%':
    case '_':
    case '-':
    case '+':
    case '=':
    case ':':
    case ',':
    case '.':
    case '/':
        return true;
    }
    return false;
}

static std::string shell_escape(const std::string& s)
{
    if (s.empty()) return s;
    bool is_safe = true;
    for (auto c: s)
        is_safe = is_safe && is_shell_safe(c);
    if (is_safe) return s;
    std::string res("'");
    for (auto c: s)
        if (c == '\'')
            res += "'\\''";
        else
            res += c;
    res += '\'';
    return res;
}

QStringList RawQueryModel::as_shell_args(bool quoted) const
{
    QStringList res;
    std::vector<rawquery::Item> new_items = record_to_items(build_record());
    for (auto item: new_items)
    {
        std::string s(item.key.c_str());
        s += "=";
        if (quoted)
            s += shell_escape(item.val);
        else
            s += item.val;
        res.append(s.c_str());
    }
    return res;
}


}