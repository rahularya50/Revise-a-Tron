/**
 * Created by rahul on 09-Mar-18.
 */

$(document).ajaxComplete(function () {
    $(".fancy-table-row").click(function () {
        $("#editor").modal();
        var name = $(this).prop('name');

    })
});