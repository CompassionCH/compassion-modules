odoo.define('image_cropper_form_tool.web_image_cropper', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require("web.Dialog");
    var ImageWidget = require('web.basic_fields').FieldBinaryImage;
    var fieldRegistry = require('web.field_registry');
    var QWeb = core.qweb;

    var imageCropper = ImageWidget.extend({
        className: 'o_img_cropper',
        tagName: 'span',
        supportedFieldTypes: ['image', 'file'],

        events: _.extend({}, ImageWidget.prototype.events, {
            'change .o_input_file': '_onChangeFile',
        }),

        init: function () {
            this._super.apply(this, arguments);
            console.log(this.attrs.options);
            var options = this.attrs.options || {};
            this.imgAspectRatio = ("imgAspectRatio" in options) ? options["imgAspectRatio"] : 1;
            this.minCropWidth = ("minCropWidth" in options) ? options["minCropWidth"] : 100;
            this.resizeWidth = ("compressionWidth" in options) ? options["compressionWidth"] : null;
            this.cropper = null;
            this.fileName = null;
        },

        _onChangeFile: function (event) {
            var self = this;
            var file = event.target.files[0];
            var reader = new FileReader();
            self.fileName = file.name;

            reader.onload = function (event) {
                var src = event.target.result;
                self._openImageCropper(src);
            };

            reader.readAsDataURL(file);
        },

        _openImageCropper: function (src) {
            var self = this;
            var $image = $('<img>', {src: src, height: '100%', width: '100%', id: 'imageToCrop'});
            var $cropperContainer = $('<div>', {class: 'image_cropper_form_tool_cropper_container'}).append($image);
            var $responsiveContainer = $('<div>', {class: 'container'}).append($cropperContainer);

            var dialog = new Dialog(this, {
                size: 'medium',
                title: 'Crop Image',
                $content: $responsiveContainer,
                buttons: [
                    {
                        text: 'Save',
                        classes: 'btn-primary',
                        click: function () {
                            var croppedCanvas = self.cropper.getCroppedCanvas();
                            var resizedImageData = self._resizeImage(croppedCanvas.toDataURL('image/jpeg'));
                            var img_data_base64 = null
                            resizedImageData.then(function(result) {
                                var imgDatas = result.split(",");
                                var imgDataBase64 = imgDatas[1];
                                var approxImgSize = 3 * (imgDataBase64.length / 4) - (imgDataBase64.match(/[=]+$/g) || []).length;
                                self.on_file_uploaded(
                                    approxImgSize,
                                    self.fileName,
                                    imgDatas[0],
                                    imgDataBase64
                                );
                            });
                            //self.render();
                            dialog.close();
                        },
                    },
                    {
                        text: 'Cancel',
                        classes: 'btn-secondary',
                        click: function () {
                            dialog.close();
                        },
                    },
                ],
            });

            // Open the dialog
            dialog.open();

            // Add the cropper to the picture
            dialog._opened.then(function () {
                self.cropper = new Cropper($image[0], {
                    aspectRatio: self.imgAspectRatio,
                    viewMode: 1,
                    dragMode: 'move',
                    zoomable: true,
                    cropBoxResizable: true,
                    minCropBoxWidth: self.minCropWidth,
                    minCropBoxHeight: self.minCropWidth * self.imgAspectRatio
                });
            });
        },

        // Compress the image
        _resizeImage: function (src) {
          return new Promise(function (resolve) {
            var image = new Image();
            image.onload = function () {
              var maxSize = 300 * 1024; // Maximum size in bytes (300 KB)
              var maxWidth = this.minCropWidth;
              var maxHeight = this.minCropWidth * this.imgAspectRatio;
              // this.resizeWidth
              var width = image.width;
              var height = image.height;

              if (width > maxWidth || height > maxHeight) {
                if (width > height) {
                  height *= maxWidth / width;
                  width = maxWidth;
                } else {
                  width *= maxHeight / height;
                  height = maxHeight;
                }
              }

              var canvas = document.createElement('canvas');
              canvas.width = width;
              canvas.height = height;

              var ctx = canvas.getContext('2d');
              ctx.drawImage(image, 0, 0, width, height);

              canvas.toBlob(
                function (blob) {
                  new Compressor(blob, {
                    quality: 0.6, // Adjust the desired quality value
                    width: self.resizeWidth,
                    maxSize: maxSize, // Set the maximum size in bytes
                    success: function (compressedBlob) {
                      var reader = new FileReader();
                      reader.onloadend = function () {
                        var compressedImageData = reader.result;
                        resolve(compressedImageData);
                      };
                      reader.readAsDataURL(compressedBlob);
                    },
                    error: function (error) {
                      // Handle the compression error
                      console.error(error);
                      resolve(null); // You can choose to resolve with null or handle the error differently
                    },
                  });
                },
                'image/jpeg',
                0.6 // Adjust the desired JPEG compression quality value
              );
            };
            image.src = src;
          }.bind(this));
        },
    });

    fieldRegistry.add('image_cropper', imageCropper);
    return {
        imageCropper: imageCropper,
    };
});