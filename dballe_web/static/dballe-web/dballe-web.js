(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class Server
{
    constructor() {
        var self = this;
    }

    _get(name, args) {
        var self = this;
        return new Promise((resolve, reject) => {
            $.ajax({
                url: "/api/1.0/" + name,
                method: "GET",
                data: args,
                dataType: "json",
                success: (data, textStatus, jqXHR) => {
                    console.debug("API GET", name, args, "→", data);
                    resolve(data);
                },
                error: (jqXHR, textStatus, errorThrown) => {
                    console.warn("API GET ERROR", name, args, "→", jqXHR, textStatus, errorThrown);
                    reject(errorThrown);
                },
            });
        });
    }

    _post(name, args) {
        var self = this;
        return new Promise((resolve, reject) => {
            $.ajax({
                url: "/api/1.0/" + name,
                method: "POST",
                data: JSON.stringify(args),
                processData: false,
                dataType: "json",
                contentType: "application/json",
                success: (data, textStatus, jqXHR) => {
                    console.debug("API POST", name, args, "→", data);
                    resolve(data);
                },
                error: (jqXHR, textStatus, errorThrown) => {
                    console.warn("API POST ERROR", name, args, "→", jqXHR, textStatus, errorThrown);
                    reject(errorThrown);
                },
            });
        });
    }

    async ping() {
        return await this._get("ping", {});
    }

    async async_ping() {
        return await this._get("async_ping", {});
    }

    async init() {
        return await this._get("init", {});
    }

    async get_data() {
        return await this._get("get_data", {});
    }

    async get_station_data(id_station) {
        return await this._get("get_station_data", {id_station: id_station});
    }

    async get_station_data_attrs(id) {
        return await this._get("get_station_data_attrs", {id: id});
    }

    async get_data_attrs(id) {
        return await this._get("get_data_attrs", {id: id});
    }

    async set_filter(filter) {
        return await this._post("set_filter", {filter: filter});
    }

    async replace_station_data(rec) {
        return await this._post("replace_station_data", {rec: rec});
    }

    async replace_data(rec) {
        return await this._post("replace_data", {rec: rec});
    }

    async set_data_limit(limit) {
        return await this._post("set_data_limit", {limit: limit});
    }

    async replace_station_data_attr(var_data, rec) {
        return await this._post("replace_station_data_attr", {var_data: var_data, rec: rec});
    }

    async replace_data_attr(var_data, rec) {
        return await this._post("replace_data_attr", {var_data: var_data, rec: rec});
    }
}

class DballeWeb
{
    constructor(options)
    {
        this.options = options;
        this.server = new window.dballeweb.Server();
        this.map = new window.dballeweb.ExplorerMap("map", options);
        this.filters = new window.dballeweb.Filters(this);
        this.data = new window.dballeweb.Data(this);
        this.tab_station = new window.dballeweb.StationTab(this, options);
        this.tab_value = new window.dballeweb.ValueTab(this, options);

        document.addEventListener("data_selected", evt => {
            const data = evt.detail.data;
            this.update_station_data(data.s).then();
            this.show_data_attrs(data, data.i).then();
        });

        document.addEventListener("keydown", evt => {
            if (evt.altKey)
            {
                if (evt.key == 'x') {
                    $("#tab-header-filter").tab("show");
                    evt.preventDefault();
                } else if (evt.key == 's') {
                    $("#tab-header-station").tab("show");
                    evt.preventDefault();
                } else if (evt.key == 'v') {
                    $("#tab-header-value").tab("show");
                    evt.preventDefault();
                }
            }
        });
    }

    async init()
    {
        var res = await this.server.init();
        this.update_explorer(res.explorer);
        await this.update_data();
    }

    async set_filter(filter)
    {
        var res = await this.server.set_filter(filter);
        this.update_explorer(res.explorer);
        await this.update_data();
    }

    update_explorer(explorer)
    {
        this.filters.update_explorer(explorer);
        this.data.update_explorer(explorer);
        $(".dballeweb-view-url").text(explorer.db_url);
        $(".dballeweb-view-filter-cmdline").text(explorer.filter_cmdline);
        this.trigger_explorer_updated(explorer)
    }

    async update_data()
    {
        var data = await this.server.get_data();
        this.data.update(data);
    }

    async replace_station_data(rec)
    {
        console.debug("replace_station_data", rec);
        var data = await this.server.replace_station_data(rec);
        this.trigger_station_data_updated(data);
    }

    async replace_data(rec)
    {
        console.debug("replace_data", rec);
        var data = await this.server.replace_data(rec);
        this.data.update(data);
    }

    async set_data_limit(limit)
    {
        console.debug("set_data_limit", limit);
        var data = await this.server.set_data_limit(limit);
        this.data.update(data);
    }

    /**
     * Ask for new station data from the server, and trigger a signal when we have it
     */
    async update_station_data(id_station)
    {
        console.debug("update_station_data", id_station);
        var data = await this.server.get_station_data(id_station);
        this.trigger_station_data_updated(data);
    }

    trigger_explorer_updated(explorer)
    {
        let new_evt = new CustomEvent("explorer_updated", {detail: {
            explorer: explorer,
        }, bubbles: false});
        document.dispatchEvent(new_evt);
    }

    trigger_station_data_updated(data)
    {
        let new_evt = new CustomEvent("station_data_updated", {detail: {
            data: data,
        }, bubbles: false});
        document.dispatchEvent(new_evt);
    }

    trigger_value_updated(var_data, attrs)
    {
        let new_evt = new CustomEvent("value_updated", {detail: {
            var_data: var_data,
            attrs: attrs,
        }, bubbles: false});
        document.dispatchEvent(new_evt);
    }

    async show_station_data_attrs(var_data, id)
    {
        console.debug("show_station_data_attrs", var_data, id);
        var data = await this.server.get_station_data_attrs(id);
        console.debug("show_station_data_attrs data:", data);
        this.trigger_value_updated(var_data, data);
    }

    async show_data_attrs(var_data, id)
    {
        console.debug("show_data_attrs", var_data, id);
        var data = await this.server.get_data_attrs(id);
        console.debug("show_data_attrs data:", data);
        this.trigger_value_updated(var_data, data);
    }

    async replace_station_data_attr(var_data, rec)
    {
        console.debug("replace_station_data_attr", var_data, rec);
        var data = await this.server.replace_station_data_attr(var_data, rec);
        this.trigger_value_updated(var_data, data);
    }

    async replace_data_attr(var_data, rec)
    {
        console.debug("replace_data_attr", var_data, rec);
        var data = await this.server.replace_data_attr(var_data, rec);
        this.trigger_value_updated(var_data, data);
    }
}

window.dballeweb = $.extend(window.dballeweb || {}, {
    Server: Server,
    DballeWeb: DballeWeb,
});

})(jQuery);
