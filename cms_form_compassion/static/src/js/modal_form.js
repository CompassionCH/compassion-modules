odoo.define('cms_form_compassion.modal_form', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');
    var core = require('web.core');
    var _t = core._t;

    var ModalForm = animation.Class.extend({
        selector: '.cms_modal_form',

        /**
         * Called when widget is started
         */
        start: function () {
            // Submit form in Javascript in order to render result inside the
            // modal
            var modal_form = this.$('form');
            var self = this;
            this.form_id = this.$el.attr('id');
            modal_form.submit(function (event) {
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
                var form_data = new FormData(this);
                // Inject form name in data to help the controller know which
                // form is submitted in case several modals are present.
                post_url += '?form_id=' + self.form_id;
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
                                var payment_compassion = result_html.find(
                                    '#payment_compassion');
                                if (payment_compassion.length) {
                                    // Special case for payment form, we
                                    // directly submit the payment form.
                                    var modal_body = self.$el.find(
                                        '.modal-body');
                                    modal_body.html(result_html.html());
                                    modal_body.find('#payment_compassion form')
                                        .submit();
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
                            var error_div = self.$el.find('#server_error');
                            if (error_div.length) {
                                error_div[0].outerHTML = formatted_mess;
                            } else {
                                self.$el.find('.above-controls').before(
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
            });
        },

        /**
         * HTML is given back by the form submission, we will inject it
         * in the page to display the result without reloading
         * @param render_result: the html to render
         */
        on_receive_back_html_result: function(render_result) {
            var new_form = $(render_result).find('#' + this.form_id).find(
                'form');
            if (new_form.length) {
                // The same page is returned, we must determine if we close
                // the modal or not, based on errors.
                if (new_form.find('.alert.alert-danger.error-msg').length) {
                    // We should replace the form content without closing
                    // the modal.
                    this.$el.find('form').html(new_form);
                    this.start();
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
                    this.$el.find('.modal-body').html(render_result);
                } else {
                    this.$el.find('.modal-body form').replaceWith(
                        content.html());
                }
            }
        }
    });
    animation.registry.modal_form = ModalForm;
    return ModalForm;
});
