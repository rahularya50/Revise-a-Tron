/**
 * Created by rahul on 09-Mar-18.
 */

var activeModalId = 0;

$(document).ajaxComplete(function () {
    $(".fancy-table-row").click(function () {
        $("#editor").modal();
        activeModalId = $(this).data("rowid");
        updateModal();
    })
});

$(document).ready(function () {
    $("#modal-edit").click(function () {
        $(".view-only").hide();
        $(".edit-only").show();
        $(".file-upload").val('');
    });

    $("#discard-changes-button").click(function () {

        $(".view-only").show();
        $(".edit-only").hide();
    });

    $("#save-changes-button").click(function () { // TODO: Update to handle case of new elements - get rowid from response?
        var form_data = new FormData();
        form_data.append("rowid", activeModalId);
        $(".simple-input").each(function () {
            form_data.append(this.dataset.column, $(this).val());
        });
        $(".file-upload").each(function () {
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
                console.log(response);
                if (response === "fail") {
                    console.log("error");
                    $("#submission-error").show();
                }
                else {
                    resync_selectors();
                    activeModalId = parseInt(response);
                }
            }
        })
    });

    $("#delete-button").click(function () {
        $.ajax({
            url: "/delete_entry?rowid=" + activeModalId,
            success: function (response) {
                $("#editor").modal("hide");
                resync_selectors()
            }
        });
    });

    $("#add-new-button").click(function () {
        activeModalId = -1;
        $("#editor").modal();
        $(".modify-only").hide();
        newModal();
    });
});

$(document).ajaxComplete(updateModal);

function updateModal() {
    if (activeModalId !== -1) {
        var activeRow = $("[data-rowid='" + activeModalId + "']");
        $(".view-only").show();
        $(".edit-only").hide();
        $(".modify-only").show();
        $(activeRow).find("td").each(function () {
            $("#" + this.dataset.column + "-indicator").html(this.dataset.value);
            $("#" + this.dataset.column + "-input").val(this.dataset.value).trigger('change');
            $("#" + this.dataset.column + "-modal-image").prop("src", this.dataset.value);
        })
    }
}

function newModal() {
    $(".view-only").hide();
    $(".edit-only").show();
    $("#submission-error").hide();
    $(".modify-only").show();
    $(".simple-input").val("").trigger('change');
    $(".modal-image").prop("src", "");
}