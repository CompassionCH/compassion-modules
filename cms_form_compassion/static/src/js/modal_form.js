odoo.define('cms_form_compassion.modal_form', function (require) {
    "use strict";
    var PaymentForm = require('payment.payment_form');
    var Widget = require("web.Widget");

    var ModalForm = Widget.extend({
        events: {
            "submit form": "submitEvent"
        },

        submitEvent: function(event) {
            var self = this;
            var modal = this.$el;
            var modal_form = modal.find("form");
            var form_id = modal.attr('id');
            // Prevent direct submission
            event.preventDefault();
            // Show spinner
            var btn = $(event.target).find('button[type="submit"]').first();
            btn.attr('data-loading-text',
                '<i class="fa fa-circle-o-notch fa-spin" ' +
                'style="margin-right: 5px;"></i>'+btn.text());
            btn.button('loading');
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
                            var payment_compassion = result_html.find('#payment_compassion');
                            if (payment_compassion.length) {
                                // Special case for payment form, we load payment JS otherwise the payment is not working.
                                var modal_body = modal.find('.modal-body');
                                modal_body.html(result_html.html());
                                modal_body.find('.o_payment_form').each(function () {
                                    var $elem = $(this);
                                    var form = new PaymentForm(null, $elem.data());
                                    form.attachTo($elem);
                                });
                                // Auto submit the payment form after 3 seconds
                                // setTimeout(function() { modal_body.find('#o_payment_form_pay').click(); }, 3000);
                            } else {
                                self.on_receive_back_html_result(result_html.html());
                            }
                            btn.button('reset');
                        });
                    } else {
                        self.on_receive_back_html_result(data);
                        btn.button('reset');
                    }
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
                            token = match[1];
                            $('input[name=\'csrf_token\']').val(token);
                        }
                    }
                    btn.button('reset');
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
                if (new_form.find('.alert.alert-danger.error-msg').length) {
                    // We should replace the form content without closing
                    // the modal.
                    new_form.submit(self.formEvent);
                    modal_form.html(new_form);
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
        }
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
            var form = new ModalForm(null, $elem.data());
            form.attachTo($elem);
        });
    });

    return ModalForm;
});
