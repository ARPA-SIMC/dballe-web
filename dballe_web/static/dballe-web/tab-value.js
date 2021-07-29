(function($) {
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode
"use strict";

class ValueTab
{
    constructor(dballeweb, options)
    {
        this.dballeweb = dballeweb;
        this.body = document.getElementById("tab-value");
        this.attrs = new window.dballeweb.Attrs(this);

        // this.tab_header = document.getElementById("tab-header-station");
        // $(this.tab_header).on("shown.bs.tab", evt => {
        //     this.map.map.invalidateSize();
        // });

        document.addEventListener("value_updated", evt => {
            this.update_value(evt.detail.var_data, evt.detail.attrs);
        });
    }

    update_value(var_data, attrs)
    {
        $("#dballeweb-attr-varcode").text(var_data.c);
        $("#dballeweb-attr-value").text(var_data.v);
        if (var_data.d === undefined)
            $("#dballeweb-attr-vartype").text("Station value");
        else
            $("#dballeweb-attr-vartype").text("Measured value");
    }
}


window.dballeweb = $.extend(window.dballeweb || {}, {
    ValueTab: ValueTab,
});

})(jQuery);
