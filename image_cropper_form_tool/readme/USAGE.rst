To use this module, you need to:

* add the widget image_cropper to your view

It's possible to parametrize the cropper with :

* minCropWidth : The smallest size possible for the crop box

* imgAspectRatio : The crop box aspect ratio should be a float but it can be a division

* compressionWidth : The size in pixel of the picture after compression

Example :

    <field name="profile_picture_img" widget="image_cropper" options="{'minCropWidth': 1}"/>
