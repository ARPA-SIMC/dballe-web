(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class StationValueEditor extends window.dballeweb.Editor
{
    constructor(dballeweb, td, dballe_station, dballe_data)
    {
        super(dballeweb, td, dballe_data);
        this.dballe_station = dballe_station;
    }

    // Save the new value
    commit()
    {
        var value = this.editor.val();

        const rec = {
            ana_id: this.dballe_station.id,
            varcode: this.dballe_data.c,
            vt: this.dballe_data.vt,
        };
        if (this.dballe_data.vt == "decimal")
            rec.value = parseFloat(value)
        else if (this.dballe_data.vt == "decimal")
            rec.value = parseInt(value)
        else
            rec.value = value;

        this.td.empty().text(value).removeData("dballeweb_editor");
        this.dballeweb.replace_station_data(rec).then();
    }
}

/**
 * Show station information
 */
class StationInfo
{
    constructor(dballeweb)
    {
        this.dballeweb = dballeweb;

        document.addEventListener("station_data_updated", evt => {
            const data = evt.detail.data;
            console.debug("show_station_data data:", data);
            this.update(data);
        });
    }

    update(data)
    {
        const station = data.station;
        $("#dballeweb-station-data-id").text(station.id);
        $("#dballeweb-station-data-repmemo").text(station.rep_memo);
        $("#dballeweb-station-data-coords").text(`${station.lat}, ${station.lon}`);
        $("#dballeweb-station-data-ident").text(station.ident ? station.ident : "-");
    }

}

/**
 * Show station values in an editable table
 */
class StationValues
{
    constructor(dballeweb)
    {
        this.dballeweb = dballeweb;
        this.tbody = $("#station-data tbody");
        this.tbody.on("click", "td", evt => {
            const station = $(evt.target.parentNode).data("dballe_station");
            const data = $(evt.target.parentNode).data("dballe_data");
            const idx = evt.target.cellIndex;
            let el = $(evt.target);
            if (idx == 1 && !el.data("dballeweb_editor"))
            {
                new StationValueEditor(this.dballeweb, el, station, data);
            } else {
                this.dballeweb.show_station_data_attrs(data, data.i).then();
            }
        });

        document.addEventListener("station_data_updated", evt => {
            const data = evt.detail.data;
            console.debug("show_station_data data:", data);
            this.update(data);
        });
    }

    update(data)
    {
        const station = data.station;
        const rows = data.rows;
        this.tbody.empty();
        for (const row of rows)
        {
            let tr = $("<tr class='d-flex'>").data("dballe_data", row).data("dballe_station", station);
            tr.append($("<td class='col-4'>").text(row.c));
            tr.append($("<td class='col-8'>").text(row.v));
            this.tbody.append(tr);
        }
    }
}

class StationTab
{
    constructor(dballeweb)
    {
        this.dballeweb = dballeweb;
        this.body = document.getElementById("tab-station");
        this.station_info = new StationInfo(dballeweb);
        this.station_data = new StationValues(dballeweb);
    }
}

window.dballeweb = $.extend(window.dballeweb || {}, {
    StationTab: StationTab,
});

})(jQuery);
