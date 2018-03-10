/**
 * Created by rahul on 09-Mar-18.
 */

$(document).ajaxComplete(function () {
    $(".fancy-table-row").click(function () {
        $("#editor").modal();
        var name = $(this).prop('name');
        $(".view-only").show();
        $(".edit-only").hide();
        $(".file-upload").val('');
        $(this).find("td").each(function () {
            $("#" + this.dataset.column + "-indicator").html(this.dataset.value);
            $("#" + this.dataset.column + "-input").val(this.dataset.value);
            $("#" + this.dataset.column + "-modal-image").prop("src", this.dataset.value);
        })
    })
});

$(document).ready(function () {
    $("#modal-edit").click(function () {
        $(".view-only").hide();
        $(".edit-only").show();
    });

    $("#save-changes-button").click(function () {
        var form_data = new FormData();
        $(".file-upload").each(function () {
            console.log(this.dataset.column);
            form_data.append(this.dataset.column, this.files[0]);
        });
        $.ajax({
            type: 'POST',
            url: '/receiver',
            processData: false,
            contentType: false,
            cache: false,
            data: form_data,
            success: function (response) {
                console.log("yay!", response);
            }
        })
    });
});