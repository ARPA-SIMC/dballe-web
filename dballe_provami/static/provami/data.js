(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class Editor
{
    constructor(provami, td, dballe_data)
    {
        this.provami = provami;
        this.td = td;
        this.dballe_data = dballe_data;
        if (dballe_data.vt == "decimal")
        {
            const step = 10 ** (-dballe_data.vs);
            this.editor = $(`<input class='data_editor' type='number' step='${step}' required>`);
        }
        else if (dballe_data.vt == "integer")
        {
            const step = 10 ** (-dballe_data.vs);
            this.editor = $(`<input class='data_editor' type='number' step='${step}' required>`);
        }
        else
            this.editor = $("<input class='data_editor' type='text' size='10' required>");
        this.editor.val(this.dballe_data.v);
        this.editor.keyup(evt => { this.on_keyup(evt) });
        this.editor.blur(evt => { this.on_blur(evt) });
        this.td.empty().append(this.editor);
        this.td.data("provami_editor", this.editor);
        this.editor.focus();
    }

    // Cancel the editing and restore the TD as it was
    rollback()
    {
        this.td.empty().text(this.dballe_data.v).removeData("provami_editor");
    }

    // Save the new value
    commit()
    {
        var value = this.editor.val();

        const rec = {
            ana_id: this.dballe_data.s,
            varcode: this.dballe_data.c,
            level: this.dballe_data.l,
            trange: this.dballe_data.t,
            datetime: this.dballe_data.d,
            vt: this.dballe_data.vt,
        };
        if (this.dballe_data.vt == "decimal")
            rec.value = parseFloat(value)
        else if (this.dballe_data.vt == "decimal")
            rec.value = parseInt(value)
        else
            rec.value = value;

        this.td.empty().text(value).removeData("provami_editor");
        this.provami.replace_data(rec).then();
    }

    on_keyup(evt)
    {
        if (evt.keyCode == 27) // ESC
        {
            this.rollback();
            evt.preventDefault();
        } else if (evt.keyCode == 13) { // Enter
            if (this.editor.val() == this.dballe_data.v)
                this.rollback();
            else
                this.commit();
            evt.preventDefault();
        }
        // TODO: move one row above/below with arrows?
    }

    on_blur(evt)
    {
        if (this.editor.val() == this.dballe_data.v)
            this.rollback();
        else
            this.commit();
    }
}

class Data
{
    constructor(provami)
    {
        this.provami = provami;
        this.tbody = $("#data tbody");
        this.tbody.on("click", "td", evt => {
            let data = $(evt.target.parentNode).data("dballe_data");
            let idx = evt.target.cellIndex;
            let el = $(evt.target);
            if (idx == 6 && !el.data("provami_editor"))
            {
                new Editor(this.provami, el, data);
            } else {
                this.provami.show_station_data(data.s).then();
                this.provami.show_data_attrs(data.i).then();
            }
        });
        this.data_limit = $("#data-limit");
        this.data_limit.change(evt => {
            let limit = this.data_limit.val();
            limit = limit == "unlimited" ? null : parseInt(limit);
            this.provami.set_data_limit(limit).then();
        });
    }

    update(data)
    {
        this.tbody.empty();

        for (var i = 0; i < data.rows.length; ++i)
        {
            var row = data.rows[i];
            var tr = $("<tr class='d-flex'>").data("dballe_data", row);
            tr.append($("<td class='col-2'>").text(row.r));
            tr.append($("<td class='col-1'>").text(row.s));
            tr.append($("<td class='col-1'>").text(row.c));
            tr.append($("<td class='col-2'>").text(row.l));
            tr.append($("<td class='col-2'>").text(row.t));
            tr.append($("<td class='col-2'>").text(row.d));
            tr.append($("<td class='col-2'>").text(row.v));
            this.tbody.append(tr);
        }
    }

    update_explorer(explorer)
    {
        $("#data-count").text(explorer.stats.count);
    }
}

class StationData
{
    constructor(provami)
    {
        this.provami = provami;
        this.tbody = $("#station-data tbody");
        /*
        this.tbody.on("click", "td", evt => {
            let data = $(evt.target.parentNode).data("dballe_data");
            let idx = evt.target.cellIndex;
            let el = $(evt.target);
            if (idx == 6 && !el.data("provami_editor"))
            {
                new Editor(this.provami, el, data);
            } else {
                this.provami.show_station_data(data.s).then();
                this.provami.show_data_attrs(data.i).then();
            }
        });
        */
    }

    update(data)
    {
        this.tbody.empty();

        for (var i = 0; i < data.rows.length; ++i)
        {
            var row = data.rows[i];
            var tr = $("<tr class='d-flex'>").data("dballe_data", row);
            tr.append($("<td class='col-4'>").text(row.c));
            tr.append($("<td class='col-8'>").text(row.v));
            this.tbody.append(tr);
        }
    }
}

class Attrs
{
    constructor(provami)
    {
        this.provami = provami;
        this.tbody = $("#attrs tbody");
        /*
        this.tbody.on("click", "td", evt => {
            let data = $(evt.target.parentNode).data("dballe_data");
            let idx = evt.target.cellIndex;
            let el = $(evt.target);
            if (idx == 6 && !el.data("provami_editor"))
            {
                new Editor(this.provami, el, data);
            } else {
                this.provami.show_station_data(data.s).then();
                this.provami.show_data_attrs(data.i).then();
            }
        });
        */
    }

    update(data)
    {
        this.tbody.empty();

        for (var i = 0; i < data.rows.length; ++i)
        {
            var row = data.rows[i];
            var tr = $("<tr class='d-flex'>").data("dballe_data", row);
            tr.append($("<td class='col-4'>").text(row.c));
            tr.append($("<td class='col-8'>").text(row.v));
            this.tbody.append(tr);
        }
    }
}

window.provami = $.extend(window.provami || {}, {
    Data: Data,
    StationData: StationData,
    Attrs: Attrs,
});

})(jQuery);
