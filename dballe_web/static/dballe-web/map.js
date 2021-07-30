(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class Stations
{
    constructor()
    {
        this.stations = new Map();
    }
}

class ExplorerStations extends Stations
{
    /**
     * Update the station list with data from an explorer
     */
    update_explorer(explorer)
    {
        let updated = [];
        let created = [];

        var update_station = (station, current) => {
            let key = station.join(":");
            let s = this.stations.get(key);
            if (s)
            {
                if (s.current != current)
                {
                    s.current = current;
                    updated.push(s);
                }
            } else {
                s = {
                    report: station[0],  // Station report
                    id: station[1],  // Station report
                    lat: station[2],     // Station latitude (float)
                    lon: station[3],     // Station longitude (float)
                    ident: station[4],   // Mobile station identifier
                    current: current,
                };
                if (s.ident)
                    s.title = `${s.ident} (${s.report})`;
                else
                    s.title = `${s.lat.toFixed(2)},${s.lon.toFixed(2)} (${s.report})`;
                this.stations.set(key, s);
                created.push(s);
            }
        };

        for (const station of explorer.stations)
            update_station(station, true);
        for (const station of explorer.stations_disabled)
            update_station(station, false);
        // TODO: remove stations no longer present

        return {
            updated: updated,
            created: created,
        };
    }
}


class CurrentStations extends Stations
{
    constructor()
    {
        super();
        // Id of the station currently displayed
        this.current_id = null;
    }

    /**
     * Update the station list with data from an explorer
     */
    update_explorer(explorer)
    {
        let updated = [];
        let created = [];

        var update_station = (station, current) => {
            let key = station.join(":");
            let s = this.stations.get(key);
            if (s)
            {
                if (s.current != current)
                {
                    s.current = current;
                    updated.push(s);
                }
            } else {
                s = {
                    report: station[0],  // Station report
                    id: station[1],  // Station report
                    lat: station[2],     // Station latitude (float)
                    lon: station[3],     // Station longitude (float)
                    ident: station[4],   // Mobile station identifier
                    current: current,
                };
                if (s.ident)
                    s.title = `${s.ident} (${s.report})`;
                else
                    s.title = `${s.lat.toFixed(2)},${s.lon.toFixed(2)} (${s.report})`;
                this.stations.set(key, s);
                created.push(s);
            }
        };

        let current_id = null;
        if (this.current != null)
            current_id = this.current.id;

        for (const station of explorer.stations)
            update_station(station, station[1] == current_id);
        for (const station of explorer.stations_disabled)
            update_station(station, station[1] == current_id);
        // TODO: remove stations no longer present

        return {
            updated: updated,
            created: created,
        };
    }

    /**
     * Change the currently selected station
     */
    set_current(station)
    {
        this.current = station;
        const current_id = station.id;
        let updated = [];
        for (let station of this.stations.values())
        {
            const is_current = station.id == current_id;
            if (station.current != is_current)
            {
                station.current = is_current;
                updated.push(station);
            }
        }
        return updated;
    }
}


class BaseMap
{
    constructor(id, options)
    {
        this.options = options;
        this.id = id;

        this.map = L.map(id, { boxZoom: false });

        // OSM base layer
        var osmUrl='http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
        var osmAttrib='Map data © OpenStreetMap contributors';
        var osm = new L.TileLayer(osmUrl, {minZoom: 1, maxZoom: 12, attribution: osmAttrib, boxZoom: false});
        this.map.addLayer(osm);

        // Show the mouse position in the map
        L.control.mousePosition({ position: "bottomright" }).addTo(this.map);

        // Alternative icon styles
        this.IconSelected = this._make_alt_icon("selected");
        //this.IconHighlighted = this._make_alt_icon("highlighted");
        //this.IconHidden = this._make_alt_icon("hidden");

        // Station markers layer
        this.markers_layer = null;

        this.needs_zoom_to_fit = true;

        document.addEventListener("explorer_updated", evt => {
            this.update_explorer(evt.detail.explorer);
        });
    }

    _make_alt_icon(type)
    {
        var self = this;
        return L.Icon.Default.extend({
            _getIconUrl: function (name) {
                if (L.Browser.retina && name === 'icon') {
                    name += '-2x';
                }
                return self.options.resource_url + "images/marker-" + type + "-" + name + ".png";
            }
        });
    }

    _redo_markers_layer(stations)
    {
        let layer = new L.markerClusterGroup({
            maxClusterRadius: 30,
            iconCreateFunction: cluster => {
                let children = cluster.getAllChildMarkers();
                let has_current = false;
                for (let i in children)
                {
                    let station = children[i].options.id;
                    has_current |= station.current;
                }

                let childCount = cluster.getChildCount();
                let c = has_current ? ' marker-cluster-current' : ' marker-cluster-normal';
                return new L.DivIcon({
                    html: '<div><span>' + childCount + '</span></div>',
                    className: 'marker-cluster' + c,
                    iconSize: new L.Point(40, 40)
                });
            }
        });

        for (let s of stations)
        {
            s.marker = L.marker(new L.LatLng(s.lat, s.lon), { title: s.title, id: s, hidden: false });
            if (s.current)
                s.marker.setIcon(new this.IconSelected());
            s.marker.on("click", evt => {
                this.trigger_select_station(evt.target.options.id);
            });
            layer.addLayer(s.marker);
        }

        if (this.markers_layer != null)
            this.map.removeLayer(this.markers_layer);
        this.markers_layer = layer;
        this.map.addLayer(layer);
    }

    update_explorer(explorer)
    {
        let res = this.stations.update_explorer(explorer);

        if (res.created.length)
            this._redo_markers_layer(res.created);
        else if (res.updated.length)
        {
            for (let s of res.updated)
            {
                this.markers_layer.removeLayer(s.marker);
                s.marker.setIcon(s.current ? new this.IconSelected() : new L.Icon.Default());
                this.markers_layer.addLayer(s.marker);
            }
            this.markers_layer.refreshClusters();
        }

        if (this.needs_zoom_to_fit)
            this.zoom_to_fit();
    }
}


/**
 * Map showing the current station in the station tab
 */
class StationMap extends BaseMap
{
    constructor(id, options)
    {
        super(id, options);

        // Station storage
        this.stations = new CurrentStations();

        document.addEventListener("station_data_updated", evt => {
            const data = evt.detail.data;
            const updated = this.stations.set_current(data.station);

            if (updated.length)
            {
                for (let s of updated)
                {
                    this.markers_layer.removeLayer(s.marker);
                    s.marker.setIcon(s.current ? new this.IconSelected() : new L.Icon.Default());
                    this.markers_layer.addLayer(s.marker);
                }
                this.markers_layer.refreshClusters();
            }

            this.zoom_to_fit();
        });
    }

    zoom_to_fit()
    {
        // Compute the bounding box of the points
        let points = [];

        if (this.stations.current != null)
            points.push([this.stations.current.lat, this.stations.current.lon]);

        // If there is no current station selected, add all stations
        if (!points.length)
        {
            for (const station of this.stations.stations.values())
            {
                points.push([station.lat, station.lon]);
            }
        }

        if (points.length)
        {
            let bounds = L.latLngBounds(points);
            this.map.fitBounds(bounds);
            this.needs_zoom_to_fit = false;
        } else
            this.needs_zoom_to_fit = true;
    }

}


/**
 * Map for station selection in the explore tab
 */
class ExplorerMap extends BaseMap
{
    constructor(id, options)
    {
        super(id, options);

        // Station storage
        this.stations = new ExplorerStations();

        // Add the rectangle selection facility
        var selectfeature = this.map.boxSelect.enable();
        this.map.on("boxselecting", (e) => {
            this.trigger_select_station_bounds(e.bounds, false);
        });
        this.map.on("boxselected", (e) => {
            this.trigger_select_station_bounds(e.bounds, true);
        });
    }

    trigger_select_station_bounds(bounds, finished)
    {
        let new_evt = new CustomEvent("map_select_station_bounds", {detail: {
            bounds: bounds,
            finished: finished,
        }, bubbles: false});
        document.dispatchEvent(new_evt);
    }

    trigger_select_station(info)
    {
        let new_evt = new CustomEvent("map_select_station", {detail: {
            info: info,
        }, bubbles: false});
        document.dispatchEvent(new_evt);
    }

    zoom_to_fit()
    {
        // Compute the bounding box of the points
        let points = [];

        // First try only with the selected stations
        for (const [k, station] of this.stations.stations.entries())
        {
            if (!station.current) continue;
            points.push([station.lat, station.lon]);
        }

        // If there are none, try with all stations
        if (!points.length)
        {
            for (const [k, station] of this.stations.stations.entries())
            {
                points.push([station.lat, station.lon]);
            }
        }

        if (points.length)
        {
            let bounds = L.latLngBounds(points);
            this.map.fitBounds(bounds);
            this.needs_zoom_to_fit = false;
        } else
            this.needs_zoom_to_fit = true;
    }
}


window.dballeweb = $.extend(window.dballeweb || {}, {
    ExplorerMap: ExplorerMap,
    StationMap: StationMap,
});

})(jQuery);
