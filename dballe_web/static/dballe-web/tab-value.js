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
    }
}


window.dballeweb = $.extend(window.dballeweb || {}, {
    ValueTab: ValueTab,
});

})(jQuery);
