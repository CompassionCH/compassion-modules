odoo.define('cms_form_compassion.modal_form', function (require) {
    "use strict";
    var DateWidget = require('cms_form.date_widget');
    var Widget = require("web.Widget");
    var core = require('web.core');
    var _t = core._t;

    var ModalForm = Widget.extend({
        events: {
            "submit form": "submitEvent"
        },

        submitEvent: function(event) {
            var self = this;
            var modal = this.$el;
            var modal_form = modal.find("form");
            var form_id = modal.attr('id');
            var button = $(event.target).find('button[type="submit"]').first();
            var fa_class = button.children('.fa').attr("class");
            if (fa_class) {
                fa_class = fa_class.split(/\s+/)[1]
            } else {
                fa_class = "";
            }
            // Prevent direct submission
            event.preventDefault();
            // Show spinner
            self.disableButton(button, fa_class);
            // Send form in ajax (remove translation url)
            var post_url = window.location.pathname;
            var form_data = new FormData(modal_form[0]);
            // Inject form name in data to help the controller know which
            // form is submitted in case several modals are present.
            post_url += '?form_id=' + form_id;
            $.ajax({
                type: 'POST',
                url: post_url,
                data: form_data,
                cache: false,
                contentType: false,
                processData: false,
                success: function (data) {
                    if (data.redirect) {
                        if (data.full_page) {
                            // Call the redirection
                            window.location.href = data.redirect;
                            return;
                        }
                        var result_html = $('<div></div>');
                        result_html.load(data.redirect, function() {
                            self.on_receive_back_html_result(result_html.html());
                        });
                    } else {
                        self.on_receive_back_html_result(data);
                    }
                    self.enableButton(button, fa_class);
                },
                error: function (data) {
                    // HTML page is sent back as error
                    // (because it's not JSON)
                    if (data.status === 200) {
                        self.on_receive_back_html_result(data.responseText);
                    } else {
                        var message = _t(
                            'An error occurred during form submission. ' +
                            'Please verify your submission or contact us ' +
                            'in case of trouble.');
                        var formatted_mess = '<div id="server_error" ' +
                            'class="alert alert-danger error-msg">' +
                            message + '</div>';
                        var error_div = modal.find('#server_error');
                        if (error_div.length) {
                            error_div[0].outerHTML = formatted_mess;
                        } else {
                            modal.find('.above-controls').before(
                                formatted_mess);
                        }
                        // Update csrf_token
                        var token_regex = /csrf_token: "(.*)"/;
                        var match = token_regex.exec(data.responseText);
                        if (match !== null) {
                            $('input[name=\'csrf_token\']').val(match[1]);
                        }
                    }
                    self.enableButton(button, fa_class);
                }
             });
        },

        on_receive_back_html_result: function(render_result){
            var self = this;
            var modal = this.$el;
            var modal_form = modal.find("form");
            var form_id = modal.attr('id');
            var new_form = $(render_result).find('#' + form_id).find('form');
            if (new_form.length) {
                // The same page is returned, we must determine if we close
                // the modal or not, based on errors.
                // TODO date pickers stop working after form error. This is not a blocking issue but could be fixed.
                // The commented code below doesn't work (attempt to load js for input)
//                var date_fields = new_form.find('.cms_form_wrapper form input.js_datepicker');
//                if (date_fields.length) {
//                    // we load payment JS otherwise the date widgets are not working.
//                    date_fields.each(function () {
//                        var $elem = $(this);
//                        var date_widget = new DateWidget(null, $elem.data());
//                        date_widget.attachTo($elem);
//                    });
//                }
                var error_div = $(render_result).find('.alert.alert-danger');
                if (error_div.length && !error_div.is(':hidden')) {
                    // We should replace the form content without closing
                    // the modal and check if the errors are visible inside the form.
                    var modal_errors = new_form.find('.alert.alert-danger.error-msg');
                    if (!modal_errors.length) {
                        new_form.find("div.form-controls").before(error_div.parent())
                    }
                    new_form.submit(self.formEvent);
                    modal_form.parent().html(new_form);
                } else {
                    // We can reload the page.
                    document.write(render_result);
                }
            } else {
                // This is another page. we load it inside the modal.
                // Try to find if it's an Odoo page an extract the content
                var content = $(render_result).find('#wrap .container');
                if (content.length === 0) {
                    content = $(render_result).find('.main_container');
                }
                if (content.length === 0) {
                    // Render the full page
                    modal.find('.modal-body').html(render_result);
                } else {
                    modal.find('.modal-body form').replaceWith(content.html());
                }
            }
        },

        disableButton: function (button, fa_class) {
            $(button).attr('disabled', true);
            $(button).children('.fa').removeClass(fa_class);
            $(button).prepend('<span class="o_loader"><i class="fa fa-refresh fa-spin"></i>&nbsp;</span>');
        },

        enableButton: function (button, fa_class) {
            $(button).attr('disabled', false);
            $(button).children('.fa').addClass(fa_class);
            $(button).find('span.o_loader').remove();
        },
    });

    $(function () {
        // TODO This was taken from payment/payment_form.js module, but apparently there could be a better way
        // of loading the widget into the view. We can see how this one will evolve maybe.
        if (!$('.cms_modal_form').length) {
            console.log("DOM doesn't contain '.cms_modal_form'");
            return;
        }
        $('.cms_modal_form').each(function () {
            var $elem = $(this);
            if (this.id !== "modal_donation") {
                console.log("Modal form JS loaded for elem " + this.id);
                var form = new ModalForm(null, $elem.data());
                form.attachTo($elem);
            }
        });
    });

    return ModalForm;
});
