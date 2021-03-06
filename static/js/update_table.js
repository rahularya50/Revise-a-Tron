/**
 * Created by rahul on 08-Mar-18.
 */

var ready = false;

$(document).ajaxComplete(function () {
    if (!ready) {
        ready = true;
        $(".table-selector").change(resync_selectors);
    }
});

$(document).ready(function () {
    resync("", true);
});

function resync(params, get_all) {
    $.ajax({
        url: "/table_gen?" + params,
        success: [function (result) {
            if (get_all) {
                $("#fancy-table").html(result);
            }
            else {
                $("#table-data").replaceWith($(result).find("#table-data"));
            }
        }]
    });
}

function resync_selectors() {
    var params = $(".table-selector").serialize();
    resync(params, false);
}
