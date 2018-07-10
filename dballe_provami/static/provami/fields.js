(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class FilterField
{
    constructor(filters, name)
    {
        this.filters = filters
        this.name = name;
        this.row = $("#filter-" + this.name);
        this.remove = this.row.find("button.remove").hide();
        this.value = null;
        this.remove.click(evt => { this.unset(); });
    }
}

/**
 * Map-related station filter field
 */
class FilterFieldStation extends FilterField
{
    constructor(filters)
    {
        super(filters, "station");
        this.map = filters.provami.map;
        this.map.controllers.push(this);
        this.field_value = this.row.find("td.value");
    }

    unset()
    {
        this.field_value.text("all");
        this.remove.hide();
    }

    _filters_to_text(filters)
    {
        var strs = [];
        for (var i in filters)
        {
            strs.push(filters[i][0] + "=" + filters[i][1]);
        }
        return strs.join(" ");
    }

    select_station(info)
    {
        console.log("Selected", info);
        var filters = [
            ["rep_memo", info.report],
            ["lat", info.lat],
            ["lon", info.lon],
        ];
        if (info.ident)
            filters["ident"] = info.ident;
        else
            filters["mobile"] = 0;
        this.field_value.text(this._filters_to_text(filters));
        this.remove.show();
    }

    select_station_bounds(bounds, finished)
    {
        console.log("Bounds", bounds, finished);
        var filter = [
            ["latmin", bounds._southWest.lat.toFixed(5)],
            ["latmax", bounds._northEast.lat.toFixed(5)],
            ["lonmin", bounds._northEast.lng.toFixed(5)],
            ["lonmax", bounds._southWest.lng.toFixed(5)],
        ];
        if (finished)
        {
            this.field_value.text(this._filters_to_text(filters));
            this.remove.show();
        }
        else
            this.field_value.html(`<i>${this._filters_to_text(filters)}</i>`);
    }

    update_explorer(explorer)
    {
        this.map.set_current_stations(explorer.stations);
    }
}


/**
 * Multiple-choice generic filter field
 */
class FilterFieldChoices extends FilterField
{
    constructor(filters, name)
    {
        super(filters, name);
        this.field = $("#filter-field-" + name);
        this.field.change(evt => {
            var args = {};
            args[this.name] = this.field.val();
            this.filters.set_filter(args).then();
        });
    }

    unset()
    {
        var args = {};
        args[this.name] = null;
        this.filters.set_filter(args).then();
    }

    _get_option(o) {
        if (o instanceof Array)
            return o;
        else
            return [o, o];
    }

    _set_forced(value)
    {
        // Only one available option, mark it as hardcoded
        value = this._get_option(value);
        this.value = null;
        this.remove.hide();
        this.row.find("td.value span.value").text(value[1]).show();
        this.field.hide();
    }

    _set_multi(options)
    {
        // Multiple available options
        this.value = null;

        // Fill the <option> list in the <select> field
        this.field.empty();
        this.field.append("<option value='' selected>-------</option>");
        for (var i = 0; i < options.length; ++i)
        {
            var o = this._get_option(options[i]);
            var opt = $("<option>").attr("value", o[0]).text(o[1]);
            this.field.append(opt);
        }

        this.remove.hide();
        this.row.find("td.value span.value").hide();
        this.field.show();
    }

    _set_chosen(value)
    {
        // Chosen: show the choice
        value = this._get_option(value);
        this.value = value[0];
        this.remove.show();
        this.row.find("td.value span.value").text(value[1]).show();
        this.field.hide();
    }

    update_explorer(explorer)
    {
        var current = explorer.filter[this.name];
        var options = explorer[this.name];
        if (current == null)
        {
            // Not currently chosen
            if (options.length == 1)
                this._set_forced(options[0]);
            else
                this._set_multi(options);
        } else
            this._set_chosen(current);
    }
}


/**
 * Manager for all filter fields
 */
class Filters
{
    constructor(provami)
    {
        this.provami = provami
        this.fields = [
            // new FilterFieldStation(this),
            new FilterFieldChoices(this, "rep_memo"),
            new FilterFieldChoices(this, "var"), // TODO: rename in varcode
            new FilterFieldChoices(this, "level"),
            new FilterFieldChoices(this, "trange"),
        ];
        this.filter = {}

        $("#filter_fields").attr("disabled", true);
        $("#filter_update").attr("disabled", true);
        $("#filter").submit(() => { return false; });
        //$("#filter").change(() => { $("#filter_update").attr("disabled", false); });
        $("#filter_update").click(evt => { this.submit_filter(); });
    }

    /**
     * Update the filters state to reflect an updated Explorer state from server
     */
    update_explorer(explorer)
    {
        console.log("New explorer state:", explorer);

        this.filter = explorer.filter;

        $.each(this.fields, (idx, el) => {
            el.update_explorer(explorer);
        });

        $("#filter-new-button").attr("disabled", !explorer.initialized);
    }

    /**
     * Update the filter setting the given values.
     *
     * filter is a dict with the filter values that need to be changed.
     */
    async set_filter(filter)
    {
        Object.assign(this.filter, filter);
        console.log("Set new filter after", filter, "→", this.filter);
        await this.provami.set_filter(this.filter);
    }
}


window.provami = $.extend(window.provami || {}, {
    Filters: Filters,
});

})(jQuery);
