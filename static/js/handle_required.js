// toggles error states for input fields that have required
var handleRequiredField = function() {
    if ($(this).val() == "") {
        $(this).closest('.form-group').removeClass('has-success');
        $(this).closest('.form-group').addClass('has-error');
    } else {
        $(this).closest('.form-group').removeClass('has-error');
        $(this).closest('.form-group').addClass('has-success');
    }
}
