#include "provami/dateedit.h"
#include "provami/model.h"
#include <QKeyEvent>
#include <sstream>

using namespace std;
using namespace dballe;

namespace provami {

DateEdit::DateEdit(QWidget *parent) :
    QLineEdit(parent),
    fmt1(R"((\d{4})(?:[/-](\d{1,2})(?:[/-](\d{1,2})(?:\s+(\d{1,2})(?::(\d{1,2})(?::(\d{1,2}))?)?)?)?)?)"),
    fmt2(R"((?:(?:(\d{1,2})[/-])?(\d{1,2})[/-])?(\d{4})(?:\s+(\d{1,2})(?::(\d{1,2})(?::(\d{1,2}))?)?)?)")
{
    connect(this, SIGNAL(editingFinished()), this, SLOT(on_editing_finished()));
    connect(this, SIGNAL(textEdited(QString)), this, SLOT(on_text_edited(QString)));
}

void DateEdit::set_model(Model &model)
{
    this->model = &model;
    connect(this->model, SIGNAL(active_filter_changed()), this, SLOT(on_minmax_changed()));
}

QDateTime DateEdit::set_value(const Datetime& dt)
{
    setStyleSheet("");
    if (dt.is_missing())
    {
        setText("");
        return QDateTime();
    }
    else
    {
        QDateTime res(QDate(dt.year, dt.month, dt.day), QTime(dt.hour, dt.minute, dt.second));
        setText(res.toString("yyyy-MM-dd hh:mm:ss"));
        return res;
    }
}

void DateEdit::keyPressEvent(QKeyEvent *event)
{
    switch(event->key())
    {
    case Qt::Key_Escape:
        reset();
        break;
    default:
        QLineEdit::keyPressEvent(event);
    }
}

static int int_or_null(const QString& s)
{
    if (s.isEmpty()) return dballe::MISSING_INT;
    return s.toInt();
}

bool DateEdit::validate(const QString &text, QDateTime& parsed)
{
    QString s(text.simplified());

    // Empty string is ok, it's the missing date
    if (s.isEmpty())
    {
        parsed = QDateTime();
        return true;
    }

    // Try all the matchers in sequence
    int vals[6];
    if (fmt1.exactMatch(s))
    {
        // y m d h m s
        vals[0] = int_or_null(fmt1.cap(1));
        vals[1] = int_or_null(fmt1.cap(2));
        vals[2] = int_or_null(fmt1.cap(3));
        vals[3] = int_or_null(fmt1.cap(4));
        vals[4] = int_or_null(fmt1.cap(5));
        vals[5] = int_or_null(fmt1.cap(6));
    } else if (fmt2.exactMatch(s)) {
        // d m y h m s
        vals[0] = int_or_null(fmt2.cap(3));
        vals[1] = int_or_null(fmt2.cap(2));
        vals[2] = int_or_null(fmt2.cap(1));
        vals[3] = int_or_null(fmt2.cap(4));
        vals[4] = int_or_null(fmt2.cap(5));
        vals[5] = int_or_null(fmt2.cap(6));
    } else {
        parsed = QDateTime();
        return false;
    }

    if (vals[0] == MISSING_INT)
    {
        // A different way of being empty? Likely this is never reached.
        parsed = QDateTime();
        return true;
    }

    complete_datetime(vals);

    QDate date(vals[0], vals[1], vals[2]);
    if (!date.isValid())
    {
        parsed = QDateTime();
        return false;
    }

    QTime time(vals[3], vals[4], vals[5]);
    if (!time.isValid())
    {
        parsed = QDateTime();
        return false;
    }

    parsed = QDateTime(date, time);
    return !parsed.isNull() && parsed.isValid();
}

void DateEdit::complete_datetime(int *vals) const
{
    if (vals[1] == MISSING_INT) vals[1] = 1;
    if (vals[2] == MISSING_INT) vals[2] = 1;
    if (vals[3] == MISSING_INT) vals[3] = 0;
    if (vals[4] == MISSING_INT) vals[4] = 0;
    if (vals[5] == MISSING_INT) vals[5] = 0;
}

void DateEdit::on_editing_finished()
{
    QDateTime parsed;
    if (validate(text(), parsed))
    {
        setText(parsed.toString("yyyy-MM-dd hh:mm:ss"));
        setStyleSheet("");
        emit activate(parsed);
    } else {
        setStyleSheet("QLineEdit{background: #fbb;}");
        reset();
    }}

void DateEdit::on_text_edited(const QString &text)
{
    QDateTime parsed;
    if (validate(text, parsed))
    {
        setStyleSheet("QLineEdit{background: #cff;}");
    } else {
        setStyleSheet("QLineEdit{background: #fbb;}");
    }
}

void MinDateEdit::on_minmax_changed()
{
    stringstream buf;
    buf << model->summary_datetime_min();
    setToolTip(QString::fromStdString(buf.str()));
}

MinDateEdit::MinDateEdit(QWidget *parent)
    : DateEdit(parent)
{
}

void MinDateEdit::reset()
{
    DatetimeRange dtr = model->next_filter->get_datetimerange();
    emit(activate(set_value(dtr.min)));
}

MaxDateEdit::MaxDateEdit(QWidget *parent)
    : DateEdit(parent)
{
}

void MaxDateEdit::reset()
{
    DatetimeRange dtr = model->next_filter->get_datetimerange();
    emit(activate(set_value(dtr.max)));
}

void MaxDateEdit::complete_datetime(int *vals) const
{
    if (vals[1] == MISSING_INT) vals[1] = 12;
    if (vals[2] == MISSING_INT) vals[2] = QDate(vals[0], vals[1], 1).daysInMonth();
    if (vals[3] == MISSING_INT) vals[3] = 23;
    if (vals[4] == MISSING_INT) vals[4] = 59;
    if (vals[5] == MISSING_INT) vals[5] = 59;
}

void MaxDateEdit::on_minmax_changed()
{
    stringstream buf;
    buf << model->summary_datetime_max();
    setToolTip(QString::fromStdString(buf.str()));
}

/*
class DateChoice(wx.TextCtrl):
    def changed(self, event):
        if self.updating: return
        valid, values = self.isValid(self.GetValue())
        self.updating = True
        if valid:
            self.SetBackgroundColour(self.defaultBackground)
            if values is not None:
                self.model.setDateTimeFilter(values[0], values[1], values[2], values[3], values[4], values[5], filter=self.type)
            else:
                self.model.setDateTimeFilter(None)
        else:
            self.SetBackgroundColour(self.invalidBackground)
            self.model.setDateTimeFilter(None, filter = self.type)
        self.updating = False

    def filterChanged(self, what):
        if self.updating: return
        if what == "datetime":
            self.updating = True
            year, month, day, hour, min, sec = self.model.getDateTimeFilter(self.type)
            if year is None:
                self.SetValue('')
            elif month is None:
                self.SetValue("%04d" % (year))
            elif day is None:
                self.SetValue("%04d-%02d" % (year, month))
            elif hour is None:
                self.SetValue("%04d-%02d-%02d" % (year, month, day))
            elif min is None:
                self.SetValue("%04d-%02d-%02d %02d" % (year, month, day, hour))
            elif sec is None:
                self.SetValue("%04d-%02d-%02d %02d:%02d" % (year, month, day, hour, min))
            else:
                self.SetValue("%04d-%02d-%02d %02d:%02d:%02d" % (year, month, day, hour, min, sec))
            self.updating = False

    def hasData(self, what):
        if what == "dtimes":
            self.min, self.max = self.model.daterange()
            self.tip.SetTip("Minimum value: " + str(self.min) + "\nMaximum value: " + str(self.max))
            self.filterChanged("datetime")
            self.changed(None)

class MinDateChoice(DateChoice, ModelListener):
    def __init__(self, parent, model):
        DateChoice.__init__(self, parent, model, type=DateUtils.MIN)

class MaxDateChoice(DateChoice, ModelListener):
    def __init__(self, parent, model):
        DateChoice.__init__(self, parent, model, type=DateUtils.MAX)
*/
}
