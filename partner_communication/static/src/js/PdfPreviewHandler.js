odoo.define('partner_compassion.ShowLoadingMessage', function (require) {
    'use strict';

    var FormController = require('web.FormController');

    FormController.include({
        start: function () {
            this._super.apply(this, arguments);
            // Initialize retry count
            this.retryCount = 0;
            this.maxRetries = 5; // Maximum number of retries
            this._checkPreviewImage();
        },
//            // Show the loading message when the form is rendered
//            this.$el.find('.pdf_loading').show();
//
//            // Hide the loading message after 1 second
//            setTimeout(() => {
//                this.$el.find('.pdf_loading').hide();
//            }, 2500);
        _checkPreviewImage: function () {
            // Find the image element associated with the 'preview' field
            var $image = this.$el.find('img[name="preview"]');

            // The load event listener
            $image.on('load', function () {
                // This function is called when the image has finished loading.
                console.log("The 'preview' image has finished loading.");
                self._onImageLoaded();
            });

            if ($image.length && $image.attr('src') && isInViewport($image[0])) {
                // The image widget has content
                console.log("The 'preview' image widget contains data.");
                this.$el.find('.pdf_loading').hide();
            } else if (this.retryCount < this.maxRetries) {
                // The image widget is empty
                console.log("The 'preview' image widget is empty.");
                this.$el.find('.pdf_loading').show();
                setTimeout(() => {
                    // Increment retry count and call the check function again
                    this.retryCount++;
                    this._checkPreviewImage();
                }, 1000);
            } else {
                // Max retries reached, stop trying
                console.log("The 'preview' image is still empty after the maximum number of retries.");
            }
        },

        _onImageLoaded: function () {
            // Hide the loading message
            this.$el.find('#loading_message').hide();
            // Additional actions upon image load can be performed here
        },

        isInViewport: function (element) {
            var rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        }
    });
});
