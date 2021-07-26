(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class Editor
{
    constructor(dballeweb, td, dballe_data)
    {
        console.debug("Editor.constructor", dballeweb, td, dballe_data);
        this.dballeweb = dballeweb;
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
        this.td.data("dballeweb_editor", this.editor);
        // This makes the element disappear on FireFox
        // this.editor.focus();
        // This seems to work:
        setTimeout(() => { this.editor.focus(); }, 0);
    }

    // Cancel the editing and restore the TD as it was
    rollback()
    {
        this.td.empty().text(this.dballe_data.v).removeData("dballeweb_editor");
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

class AttrsEditor extends Editor
{
    constructor(dballeweb, td, var_data, dballe_data)
    {
        super(dballeweb, td, dballe_data);
        this.var_data = var_data;
    }

    // Save the new value
    commit()
    {
        var value = this.editor.val();

        const rec = {
            c: this.dballe_data.c,
            vt: this.dballe_data.vt,
            vs: this.dballe_data.vs,
        };
        if (this.dballe_data.vt == "decimal")
            rec.v = parseFloat(value)
        else if (this.dballe_data.vt == "decimal")
            rec.v = parseInt(value)
        else
            rec.v = value;

        this.td.empty().text(value).removeData("dballeweb_editor");
        if (this.var_data.d)
            this.dballeweb.replace_data_attr(this.var_data, rec).then();
        else
            this.dballeweb.replace_station_data_attr(this.var_data, rec).then();
    }
}

class DataEditor extends Editor
{
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

        this.td.empty().text(value).removeData("dballeweb_editor");
        this.dballeweb.replace_data(rec).then();
    }
}

class Data
{
    constructor(dballeweb)
    {
        this.dballeweb = dballeweb;
        this.tbody = $("#data tbody");
        this.tbody.on("click", "td", evt => {
            let data = $(evt.target.parentNode).data("dballe_data");
            let idx = evt.target.cellIndex;
            let el = $(evt.target);
            this.trigger_data_selected(data);
            if (idx == 6 && !el.data("dballeweb_editor"))
            {
                // TODO: convert into a signal
                new DataEditor(this.dballeweb, el, data);
            }
        });
        this.data_limit = $("#data-limit");
        this.data_limit.change(evt => {
            let limit = this.data_limit.val();
            limit = limit == "unlimited" ? null : parseInt(limit);
            this.dballeweb.set_data_limit(limit).then();
        });
    }

    trigger_data_selected(data)
    {
        let new_evt = new CustomEvent("data_selected", {detail: {
            data: data,
        }, bubbles: false});
        document.dispatchEvent(new_evt);
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

class Attrs
{
    constructor(dballeweb)
    {
        this.dballeweb = dballeweb;
        this.tbody = $("#attrs tbody");
        this.tbody.on("click", "td", evt => {
            let var_data = $(evt.target.parentNode).data("dballe_var_data");
            let data = $(evt.target.parentNode).data("dballe_data");
            let idx = evt.target.cellIndex;
            let el = $(evt.target);
            if (idx == 1 && !el.data("dballeweb_editor"))
                new AttrsEditor(this.dballeweb, el, var_data, data);
        });
    }

    update(var_data, data)
    {
        console.debug("Attrs.update", var_data, data)
        $("#dballeweb-attr-varcode").text(var_data.c);
        $("#dballeweb-attr-value").text(var_data.v);

        this.tbody.empty();
        for (var i = 0; i < data.rows.length; ++i)
        {
            var row = data.rows[i];
            var tr = $("<tr class='d-flex'>").data("dballe_data", row).data("dballe_var_data", var_data);
            tr.append($("<td class='col-4'>").text(row.c));
            tr.append($("<td class='col-8'>").text(row.v));
            this.tbody.append(tr);
        }
    }
}

window.dballeweb = $.extend(window.dballeweb || {}, {
    Data: Data,
    Attrs: Attrs,
    Editor: Editor,
});

})(jQuery);
