(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class FilterField
{
    constructor(filters, name)
    {
        this.filters = filters
        this.name = name;
        this.container = $("#filter-" + this.name);
        this.remove = this.container.find(".dballeweb-remove").hide();
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
        this.field_value = this.container.find(".dballeweb-value");
        document.addEventListener("map_select_station", evt => {
            this.select_station(evt.detail.info);
        });
        document.addEventListener("map_select_station_bounds", evt => {
            this.select_station_bounds(evt.detail.bounds, evt.detail.finished);
        });
    }

    unset()
    {
        this.field_value.text("all");
        this.remove.hide();
        this.value = {};
        this.filters.update_filter().then();
    }

    _filters_to_text(filters)
    {
        let strs = [];
        for (let i of filters)
        {
            strs.push(i[0] + "=" + i[1]);
        }
        return strs.join(" ");
    }

    _set_value(filters)
    {
        this.field_value.text(this._filters_to_text(filters));
        this.value = {};
        for (let f of filters)
            this.value[f[0]] = f[1];
        this.remove.show();
    }

    select_station(info)
    {
        var filters = [
            ["ana_id", info.id],
        ];
        this._set_value(filters);
        this.filters.update_filter().then();
        // TODO: trigger events instead
        this.filters.dballeweb.update_station_data(info.id).then();
    }

    select_station_bounds(bounds, finished)
    {
        var filters = [
            ["latmin", bounds._southWest.lat.toFixed(5)],
            ["latmax", bounds._northEast.lat.toFixed(5)],
            ["lonmin", bounds._southWest.lng.toFixed(5)],
            ["lonmax", bounds._northEast.lng.toFixed(5)],
        ];
        if (finished)
        {
            this._set_value(filters);
            this.filters.update_filter().then();
        }
        else
            this.field_value.html(`<i>${this._filters_to_text(filters)}</i>`);
    }

    update_explorer(explorer)
    {
        if (explorer.filter.ana_id)
        {
            this._set_value([
                ["ana_id", explorer.filter.ana_id],
            ]);
        }
        else if (explorer.filter.latmin)
        {
            this._set_value([
                ["latmin", parseFloat(explorer.filter.latmin)],
                ["latmax", parseFloat(explorer.filter.latmax)],
                ["lonmin", parseFloat(explorer.filter.lonmin)],
                ["lonmax", parseFloat(explorer.filter.lonmax)],
            ]);
        }
        else
            this.value = {}
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
            let option = $(evt.target).find("option:selected");
            const value = option.data("dballe_value");
            this.value = {};
            this.value[this.name] = value;
            this.filters.update_filter().then();
        });
    }

    unset()
    {
        this.value = {};
        this.filters.update_filter().then();
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
        this.value = {};
        this.remove.hide();
        this.container.find(".dballeweb-value").text(value[1]).show();
        this.field.hide();
    }

    _set_multi(options)
    {
        // Multiple available options
        this.value = {};

        // Fill the <option> list in the <select> field
        this.field.empty();
        this.field.append("<option value='' selected>-------</option>");
        for (var i = 0; i < options.length; ++i)
        {
            var o = this._get_option(options[i]);
            var opt = $("<option>").attr("value", o[0]).text(o[1]).data("dballe_value", o[0]);
            this.field.append(opt);
        }

        this.remove.hide();
        this.container.find(".dballeweb-value").hide();
        this.field.show();
    }

    _set_chosen(value)
    {
        // Chosen: show the choice
        value = this._get_option(value);
        this.value = {};
        this.value[this.name] = value[0];
        this.remove.show();
        this.container.find(".dballeweb-value").text(value[1]).show();
        this.field.hide();
    }

    update_explorer(explorer)
    {
        let current = explorer.filter[this.name];
        let options = explorer[this.name];
        if (current == null)
        {
            // Not currently chosen
            if (options.length == 1)
                this._set_forced(options[0]);
            else
                this._set_multi(options);
        } else {
            this._set_chosen(current);
        }
    }
}


/**
 * Date-time filter
 */
class FilterFieldDateTime extends FilterField
{
    constructor(filters)
    {
        super(filters, "datetime");
        this.field_min = $("#filter-field-datetime-min");
        this.field_max = $("#filter-field-datetime-max");
        this.field_min.change(evt => { this.on_change(evt); });
        this.field_max.change(evt => { this.on_change(evt); });
    }

    unset()
    {
        this.value = {};
        this.filters.update_filter().then();
    }

    on_change(evt)
    {
        this.value = {
            datemin: this.complete_value_min(this.field_min.val()),
            datemax: this.complete_value_max(this.field_max.val()),
        }
        this.filters.update_filter().then();
    }

    parse_value(val)
    {
        let re = /([0-9]{4})(?:-([0-9]+)(?:-([0-9]+)(?: ([0-9]+)(?::([0-9]+)(?::([0-9]+))?)?)?)?)?/;
        let parsed = re.exec(val);
        if (!parsed) return null;
        return parsed;
    }

    format_parsed(val)
    {
        const pad = (num, digits) => { return num.toString().padStart(digits, "0"); };
        return `${pad(val[0], 4)}-${pad(val[1], 2)}-${pad(val[2], 2)} ${pad(val[3], 2)}:${pad(val[4], 2)}:${pad(val[5], 2)}`;
    }

    complete_value_min(val)
    {
        let parsed = this.parse_value(val);
        if (!parsed) return null;
        let full = [0, 1, 1, 0, 0, 0];
        for (var i = 0; i < 6; ++i)
            if (parsed[i + 1] !== undefined)
                full[i] = parsed[i + 1];
        return this.format_parsed(full);
    }

    complete_value_max(val)
    {
        let parsed = this.parse_value(val);
        if (!parsed) return null;
        let full = [0, 12, 31, 23, 59, 59];
        for (var i = 0; i < 6; ++i)
            if (parsed[i + 1] !== undefined)
                full[i] = parsed[i + 1];
            else if (i == 2)
                full[i] = new Date(full[0], full[1], 0).getDate();
        return this.format_parsed(full);
    }

    update_explorer(explorer)
    {
        this.value = {
            datemin: explorer.filter.datemin,
            datemax: explorer.filter.datemax,
        };
        this.field_min.attr("placeholder", explorer.stats.datetime_min);
        this.field_max.attr("placeholder", explorer.stats.datetime_max);

        let has_value = false;

        if (explorer.filter.datemin)
        {
            has_value = true;
            this.field_min.val(explorer.filter.datemin);
        } else
            this.field_min.val(null);

        if (explorer.filter.datemax)
        {
            has_value = true;
            this.field_max.val(explorer.filter.datemax);
        } else
            this.field_max.val(null);

        if (has_value)
            this.remove.show();
        else
            this.remove.hide();
    }
}


/**
 * Manager for all filter fields
 */
class Filters
{
    constructor(dballeweb)
    {
        this.dballeweb = dballeweb
        this.fields = [
            new FilterFieldStation(this),
            new FilterFieldChoices(this, "rep_memo"),
            new FilterFieldChoices(this, "var"), // TODO: rename in varcode
            new FilterFieldChoices(this, "level"),
            new FilterFieldChoices(this, "trange"),
            new FilterFieldDateTime(this),
        ];

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
        console.log("Filters: new explorer state:", explorer);

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
    async update_filter()
    {
        let filter = {};
        for (let field of this.fields)
            Object.assign(filter, field.value);
        console.log("Filters: set new filter", filter);
        await this.dballeweb.set_filter(filter);
    }
}


window.dballeweb = $.extend(window.dballeweb || {}, {
    Filters: Filters,
});

})(jQuery);
