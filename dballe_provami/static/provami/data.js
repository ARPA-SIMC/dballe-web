(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class Editor
{
    constructor(provami, td)
    {
        this.provami = provami;
        this.td = td;
        this.orig = this.td.text();
        this.editor = $("<input type='text' size='10'>").val(this.orig);
        this.editor.change(evt => { this.on_change(evt) });
        this.editor.keyup(evt => { this.on_keyup(evt) });
        this.td.empty().append(this.editor);
        this.td.data("provami_editor", this.editor);
        this.editor.focus();
    }

    // Cancel the editing and restore the TD as it was
    abort()
    {
        this.td.empty().text(orig).removeData("provami_editor");
    }

    on_change(evt)
    {
        if (this.editor.val() == this.orig)
        {
            this.abort();
            evt.preventDefault();
            return;
        }
        // TODO: collect station ID, datetime, level, time range, varcode, from the row
        this.provami.set_value({}, this.editor.val()).then();
    }

    on_keyup(evt)
    {
        if (evt.keyCode == 27) // ESC
        {
            this.abort();
            evt.preventDefault();
        } else if (evt.keyCode == 13 && editor.val() == orig) { // Enter
            this.abort();
            evt.preventDefault();
        }
    }
}

class Data
{
    constructor(provami)
    {
        this.provami = provami;
        this.tbody = $("#data tbody");
        this.tbody.on("click", "td", evt => {
            let idx = evt.target.cellIndex;
            let id = $(evt.target.parentNode).data("dballe-id");
            let el = $(evt.target);
            console.log(idx, id, evt, el)
            if (idx == 6 && !el.data("provami_editor"))
            {
                new Editor(this.provami, el);
            }
        });
    }

    update(data)
    {
        this.tbody.empty();

        for (var i = 0; i < data.rows.length; ++i)
        {
            var row = data.rows[i];
            var tr = $("<tr>").data("dballe-id", row[0]);
            tr.append($("<td>").text(row[1]));
            tr.append($("<td>").text(row[2]));
            tr.append($("<td>").text(row[3]));
            tr.append($("<td>").text(row[4]));
            tr.append($("<td>").text(row[5]));
            tr.append($("<td>").text(row[6]));
            tr.append($("<td>").text(row[7]));
            this.tbody.append(tr);
        }
    }
}

window.provami = $.extend(window.provami || {}, {
    Data: Data,
});

})(jQuery);
