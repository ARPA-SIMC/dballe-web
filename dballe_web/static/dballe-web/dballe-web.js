(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class Server
{
    constructor() {
        var self = this;
    }

    /*
    _on_message(msg) {
        var self = this;
        var parsed = $.parseJSON(msg.data);
        // console.log("Message:", parsed);
        if (parsed.channel == "events")
        {
          if (parsed.type == "new_filter")
            self.events.new_filter.trigger(parsed);
        }
    }
    */

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
}

class DballeWeb
{
    constructor(options)
    {
        this.options = options;
        this.server = new window.dballeweb.Server();
        this.map = new window.dballeweb.Map("map", options);
        this.filters = new window.dballeweb.Filters(this);
	this.data = new window.dballeweb.Data(this);
	this.station_data = new window.dballeweb.StationData(this);
	this.attrs = new window.dballeweb.Attrs(this);
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
    }

    async update_data()
    {
        var data = await this.server.get_data();
	this.data.update(data);
    }

    async replace_station_data(rec)
    {
	console.log("replace_station_data", rec);
	var data = await this.server.replace_station_data(rec);
	this.station_data.update(data);
    }

    async replace_data(rec)
    {
	console.log("replace_data", rec);
	var data = await this.server.replace_data(rec);
	this.data.update(data);
    }

    async set_data_limit(limit)
    {
	console.log("set_data_limit", limit);
	var data = await this.server.set_data_limit(limit);
	this.data.update(data);
    }

    async show_station_data(id_station)
    {
        console.log("show_station_data", id_station);
        var data = await this.server.get_station_data(id_station);
        console.log("show_station_data data:", data);
	this.station_data.update(data);
    }

    async show_station_data_attrs(var_data, id)
    {
        console.log("show_station_data_attrs", var_data, id);
        var data = await this.server.get_station_data_attrs(id);
        console.log("show_station_data_attrs data:", data);
	this.attrs.update(var_data, data);
    }

    async show_data_attrs(var_data, id)
    {
        console.log("show_data_attrs", var_data, id);
        var data = await this.server.get_data_attrs(id);
        console.log("show_data_attrs data:", data);
	this.attrs.update(var_data, data);
    }
}

window.dballeweb = $.extend(window.dballeweb || {}, {
    Server: Server,
    DballeWeb: DballeWeb,
});

})(jQuery);
