/**
 * Created by rahul on 08-Mar-18.
 */

$(document).ajaxComplete(function () {
    $(".table-selector").change(function () {
        var params = $(".table-selector").serialize();
        console.log(params);
        resync(params, false);
    });
});

$(document).ready(function () {
    resync("", true);
});

function resync(params, get_all) {
    $.ajax({
        url: "/table_gen?sentinel=0&" + params,
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