(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class Stations
{
    constructor()
    {
        this.stations = {};
    }

    update_explorer(explorer)
    {
        let updated = [];
        let created = [];

        var update_station = (station, current) => {
            let key = station.join(":");
            let s = this.stations[key];
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
                    lat: station[1],     // Station latitude (float)
                    lon: station[2],     // Station longitude (float)
                    ident: station[3],   // Mobile station identifier
                    current: current,
                };
                if (s.ident)
                    s.title = `${s.ident} (${s.report})`;
                else
                    s.title = `${s.lat.toFixed(2)},${s.lon.toFixed(2)} (${s.report})`;
                this.stations[key] = s;
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


class Map
{
    constructor(id, options)
    {
        this.options = options;

        // Track station changes
        this.stations = new Stations();

        // Objects that are notified of user events
        this.controllers = [];

        // Alternative icon styles
        this.IconSelected = this._make_alt_icon("selected");
        //this.IconHighlighted = this._make_alt_icon("highlighted");
        //this.IconHidden = this._make_alt_icon("hidden");

        this.map = L.map(id, { boxZoom: false });

        // OSM base layer
        var osmUrl='http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
        var osmAttrib='Map data © OpenStreetMap contributors';
        var osm = new L.TileLayer(osmUrl, {minZoom: 1, maxZoom: 12, attribution: osmAttrib, boxZoom: false});
        this.map.addLayer(osm);

        // Show the mouse position in the map
        L.control.mousePosition({ position: "bottomright" }).addTo(this.map);

        // Station markers layer
        this.markers_layer = null;

        // Add the rectangle selection facility
        var selectfeature = this.map.boxSelect.enable();
        this.map.on("boxselecting", (e) => {
            $.each(this.controllers, (idx, c) => { c.select_station_bounds(e.bounds, false); });
        });
        this.map.on("boxselected", (e) => {
            $.each(this.controllers, (idx, c) => { c.select_station_bounds(e.bounds, true); });
        });
        this.initial = true;
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
                for (let c of this.controllers)
                    c.select_station(evt.target.options.id);
            });
            layer.addLayer(s.marker);
        }

        if (this.markers_layer != null)
            this.map.removeLayer(this.markers_layer);
        this.markers_layer = layer;
        this.map.addLayer(layer);
    }

    zoom_to_fit()
    {
        // Compute the bounding box of the points
        let points = [];
        for (const k in this.stations.stations)
        {
            const station = this.stations.stations[k];
            if (!station.current) continue;
            points.push([station.lat, station.lon]);
        }
        let bounds = L.latLngBounds(points);
        this.map.fitBounds(bounds);
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

        if (this.initial)
        {
            this.zoom_to_fit();
            this.initial = false;
        }
    }
}


window.provami = $.extend(window.provami || {}, {
    Map: Map,
});

})(jQuery);
