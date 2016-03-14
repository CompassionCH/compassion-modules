openerp.sync_mail_multi_attach = function (session){
    var QWeb = session.web.qweb;
    var _t = session.web._t;

    session.mail.ThreadComposeMessage.include({
        on_attachment_change: function (event) {
            event.stopPropagation();
            var self = this;
            var $target = $(event.target);
            if ($target.val() !== '') {

                var filename = $target.val().replace(/.*[\\\/]/,'');

                // if the files exits for this answer, delete the file before upload
                var attachments=[];
                for (var i in this.attachment_ids) {
                    if ((this.attachment_ids[i].filename || this.attachment_ids[i].name) == filename) {
                        if (this.attachment_ids[i].upload) {
                            return false;
                        }
                        this.ds_attachment.unlink([this.attachment_ids[i].id]);
                    } else {
                        attachments.push(this.attachment_ids[i]);
                    }
                }
                this.attachment_ids = attachments;

                // submit file
                _.each($target[0].files, function(file){
                    var querydata = new FormData();
                    querydata.append('callback', 'oe_fileupload_temp2');
                    querydata.append('ufile',file);
                    querydata.append('model', 'mail.compose.message');
                    querydata.append('id', '0');
                    querydata.append('multi', 'true');
                    $.ajax({
                        url: '/web/binary/upload_attachment',
                        type: 'POST',
                        data: querydata,
                        cache: false,
                        processData: false,  
                        contentType: false,
                        success: function(id){
                            self.attachment_ids.push({
                                'id': parseInt(id),
                                'name': file.name,
                                'filename': filename.name,
                                'url': '',
                                'upload': false
                            });
                            self.display_attachments();
                        },
                    });

                });
            }
        },
    });

    session.web.form.FieldMany2ManyBinaryMultiFiles.include({
        on_file_change: function (event) {
            event.stopPropagation();
            var self = this;
            var $target = $(event.target);
            if ($target.val() !== '') {
                var filename = $target.val().replace(/.*[\\\/]/,'');
                // don't uplode more of one file in same time
                if (self.data[0] && self.data[0].upload ) {
                    return false;
                }
                for (var id in this.get('value')) {
                    // if the files exits, delete the file before upload (if it's a new file)
                    if (self.data[id] && (self.data[id].filename || self.data[id].name) == filename && !self.data[id].no_unlink ) {
                        self.ds_file.unlink([id]);
                    }
                }

                // block UI or not
                if(this.node.attrs.blockui>0) {
                    instance.web.blockUI();
                }

                // TODO : unactivate send on wizard and form
                _.each($target[0].files, function(file){
                    var querydata = new FormData();
                    querydata.append('callback', 'oe_fileupload_temp2');
                    querydata.append('ufile',file);
                    querydata.append('model', 'mail.compose.message');
                    querydata.append('id', '0');
                    querydata.append('multi', 'true');
                    $.ajax({
                        url: '/web/binary/upload_attachment',
                        type: 'POST',
                        data: querydata,
                        cache: false,
                        processData: false,  
                        contentType: false,
                        success: function(id){
                            self.data[id] = {
                                'id': parseInt(id),
                                'name': file.name,
                                'filename': filename.name,
                                'url': '',
                                'upload': false
                            };
                        },
                    });

                });
                // submit file
                this.$('form.oe_form_binary_form').submit();
            }
        },
        on_file_loaded: function (event, result) {
            if(this.node.attrs.blockui>0) {
                instance.web.unblockUI();
            }

            if (result.error || !result.id ) {
                this.do_warn( _t('Uploading Error'), result.error);
                delete this.data[0];
            } else {
                var values = []
                _.each(this.data, function(file){
                     values.push(file.id);
                });
                this.set({'value': values});                
            }
            this.render_value();
        },  
    });

    session.mail.MessageCommon.include({
        display_attachments: function () {
            this._super.apply(this, arguments);
            this.$(".download-all-attachment").html( session.web.qweb.render('download.all.attachment', {'widget': this}) );
        }
    });
}
