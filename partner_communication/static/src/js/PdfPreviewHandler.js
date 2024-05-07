odoo.define("partner_compassion.ShowLoadingMessage", function (require) {
  "use strict";

  var FormController = require("web.FormController");

  var isInViewport = function (element) {
    var rect = element.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <=
        (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
  };

  FormController.include({
    start: function () {
      this._super.apply(this, arguments);
      // Initialize retry count
      this.retryCount = 0;
      // Maximum number of retries
      this.maxRetries = 5;
      this._checkPreviewImage();
    },
    _checkPreviewImage: function () {
      // Find the image element associated with the 'preview' field
      var $image = this.$el.find('img[name="preview"]');

      if ($image.length && $image.attr("src") && isInViewport($image[0])) {
        // The image widget has content
        console.log("The 'preview' image widget contains data.");
        this.$el.find(".pdf_loading").hide();
      } else if (this.retryCount < this.maxRetries) {
        // The image widget is empty
        console.log("The 'preview' image widget is empty.");
        this.$el.find(".pdf_loading").show();
        setTimeout(() => {
          // Increment retry count and call the check function again
          this.retryCount++;
          this._checkPreviewImage();
        }, 1000);
      } else {
        // Max retries reached, stop trying
        console.log(
          "The 'preview' image is still empty after the maximum number of retries."
        );
      }
    },
  });
});
