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

    async set_filter(filter) {
        return await this._post("set_filter", {filter: filter});
    }

    async replace_data(rec) {
        return await this._post("replace_data", {rec: rec});
    }

    async set_data_limit(limit) {
        return await this._post("set_data_limit", {limit: limit});
    }
}

class Provami
{
    constructor(options)
    {
        this.options = options;
        this.server = new window.provami.Server();
        this.map = new window.provami.Map("map", options);
        this.filters = new window.provami.Filters(this);
	this.data = new window.provami.Data(this);
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
        $(".provami-view-url").text(explorer.db_url);
        $(".provami-view-filter-cmdline").text(explorer.filter_cmdline);
    }

    async update_data()
    {
        var data = await this.server.get_data();
	this.data.update(data);
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
}

window.provami = $.extend(window.provami || {}, {
    Server: Server,
    Provami: Provami,
});

})(jQuery);
