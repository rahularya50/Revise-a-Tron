/**
 * Created by rahul on 09-Mar-18.
 */

$(document).ajaxComplete(function () {
    $(".fancy-table-row").click(function () {
        $("#editor").modal();
        var name = $(this).prop('name');
        console.log("clicked");
        $(this).find("td").each(function () {
            console.log(this.dataset);
            console.log("updating", this.dataset.column, this.dataset.value);
            $("#" + this.dataset.column + "-indicator").html(this.dataset.value);
        })
    })
});