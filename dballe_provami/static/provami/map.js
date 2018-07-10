(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class Map
{
    constructor(id, options)
    {
        this.options = options;
        // Alternative icon styles
        this.IconSelected = this._make_alt_icon("selected");
        //this.IconHighlighted = this._make_alt_icon("highlighted");
        //this.IconHidden = this._make_alt_icon("hidden");

        this.controllers = [];

        // Station markers layer
        this.stations_layer = null;
        // Station markers indexed by station ana_id
        // TODO this.stations_by_id = {};
        // Stations available in the current query results
        this.stations_current = {};

        this.map = L.map(id, { boxZoom: false });

        // OSM base layer
        var osmUrl='http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
        var osmAttrib='Map data © OpenStreetMap contributors';
        var osm = new L.TileLayer(osmUrl, {minZoom: 1, maxZoom: 12, attribution: osmAttrib, boxZoom: false});
        this.map.addLayer(osm);

        // Show the mouse position in the map
        L.control.mousePosition({ position: "bottomright" }).addTo(this.map);

        // Add the rectangle selection facility
        var selectfeature = this.map.boxSelect.enable();
        this.map.on("boxselecting", (e) => {
            $.each(this.controllers, (idx, c) => { c.select_station_bounds(e.bounds, false); });
        });
        this.map.on("boxselected", (e) => {
            $.each(this.controllers, (idx, c) => { c.select_station_bounds(e.bounds, true); });
        });
        //var selectfeature = map.selectAreaFeature.enable();
        //var locationFilter = new L.LocationFilter({ buttonPosition: "bottomleft", adjustButton: null }).addTo(map);
        /*
        locationFilter.on("change", function(e) {
          window.provami.js_area_selected(e.bounds.getNorth(), e.bounds.getSouth(), e.bounds.getWest(), e.bounds.getEast());
        });
        locationFilter.on("enabled", function(e) {
          window.provami.js_area_selected(e.bounds.getNorth(), e.bounds.getSouth(), e.bounds.getWest(), e.bounds.getEast());
        });
        locationFilter.on("disabled", function(e) {
          window.provami.js_area_unselected();
        });
        */
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

    _make_markers_layer()
    {
        return new L.markerClusterGroup({
            maxClusterRadius: 30,
            iconCreateFunction: cluster => {
                var children = cluster.getAllChildMarkers();
                var is_hidden = true;
                var has_current = false;
                //var has_highlighted = false;
                for (var i in children)
                {
                    var id = children[i].options.id;
                    is_hidden &= children[i].options.hidden;
                    has_current |= !!this.stations_current[id];
                    //has_highlighted |= (marker_highlighted && marker_highlighted.options.id == id);
                }

                //return new L.DivIcon({ html: '<b>' + cluster.getChildCount() + '</b>' });
                var childCount = cluster.getChildCount();

                var c = ' marker-cluster-';
                if (is_hidden)
                    c += "hidden";
                else if (has_current)
                    c += "current";
                /*
                else if (has_highlighted)
                    c += "highlighted";
                */
                else
                    c += "normal";

                return new L.DivIcon({ html: '<div><span>' + childCount + '</span></div>', className: 'marker-cluster' + c, iconSize: new L.Point(40, 40) });
            }
        });
    }

    /**
     * Replace all the stations on the map with the ones in data.
     *
     * Data is a list of station information, as follows:
     * data = [
     *      [id, lat, lon, selected, hidden],
     * ];
     */
    set_stations(stations)
    {
        var first_show = this.stations_layer == null;
        if (this.stations_layer != null)
            this.map.removeLayer(this.stations_layer);

        this.stations_layer = null;
        // TODO this.stations_by_id = {};

        if (!stations.length) return;

        this.stations_layer = this._make_markers_layer();
        var points = [];

        // Compute the bounding box of the points
        for (var i = 0; i < stations.length; ++i)
        {
            var report = stations[i][0];  // Station report
            var lat = stations[i][1];     // Station latitude (float)
            var lon = stations[i][2];     // Station longitude (float)
            var ident = stations[i][3];   // Mobile station identifier
            var title;
            if (ident)
                title = `${ident} (${report})`;
            else
                title = `${lat.toFixed(2)},${lon.toFixed(2)} (${report})`;
            points.push([lat, lon]);
            var marker = L.marker(new L.LatLng(lat, lon), { title: title, id: { report: report, lat: lat, lon: lon, ident: ident }, hidden: false });
            // TODO this.stations_by_id[id] = marker;
            marker.on("click", evt => {
                // if (evt.target.options.hidden) return;
                // select_marker(evt.target.options.id);
                $.each(this.controllers, (idx, c) => { c.select_station(evt.target.options.id); });
            });
            this.stations_layer.addLayer(marker);
            // This will remove and add it again to cause an update; it seems to cause
            // no harm at the moment, so I'll go for code reuse instead of optimization
            //update_marker(marker);
        }

        this.map.addLayer(this.stations_layer);

        if (first_show)
        {
            var bounds = L.latLngBounds(points);
            this.map.fitBounds(bounds);
        }
    }

    set_current_stations(ids)
    {
        if (!this.stations_layer)
            throw "Map.set_current_stations called before Map.set_stations";
        var c = {};
        for (var i = 0; i < ids.length; ++i)
            c[ids[i]] = true;
        /* TODO
        $.each(this.stations_by_id, (id, marker) => {
            if (c[id])
                marker.setIcon(new this.IconSelected);
            else
                marker.setIcon(new L.Icon.Default);
        });
        */
        this.stations_current = c;
        this.stations_layer.refreshClusters();
    }
}

window.provami = $.extend(window.provami || {}, {
    Map: Map,
});

})(jQuery);
