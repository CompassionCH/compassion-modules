openerp.sponsorship_tracking = function (instance) { 
    var _t = instance.web._t
    instance.web.sponsorship_tracking = instance.web.sponsorship_tracking || {};
    
    instance.web.views.add('kanban', 'instance.web_kanban.SDSTrackingKanban');
    instance.web_kanban.SDSTrackingKanban = instance.web_kanban.KanbanView.extend({
        template: "KanbanView",

        do_add_groups: function(groups) {
            var ordered_groups = groups;
            var order = []
            if(this.group_by_field.type == 'selection') {
                var selection = this.group_by_field.selection
                for (index in selection) {
                    order[index] = selection[index][0];
                }
                ordered_groups.sort(function(a, b){
                    return order.indexOf(a.value)-order.indexOf(b.value)
                });
            }
            res = this._super(ordered_groups);
            
            for (index = 0; index < groups.length; index++){
                visible_on_groups = [];
                label = ''
                action = ''

                if (this.group_by == 'sds_state'){
                    visible_on_groups = ['start', 'waiting_welcome', 'inform_no_sub'];
                    label = _t('Mail sent')
                    action = 'button_mail_sent'
                }
                if (this.group_by == 'project_state') {
                    visible_on_groups = ['inform_suspended', 'inform_reactivation', 'inform_project_terminated', 'inform_extension', 'inform_suspended_reactivation'];
                    label = _t('Project mail sent')
                    action = 'button_project_mail_sent'
                }
                if (this.group_by == 'gmc_state') {
                    label = _t('Reset GMC Status')
                    action = 'button_reset_gmc_state'
                }
     
                this.add_group_buttons(groups[index], label, action, visible_on_groups);
            }
            return res
        },
        add_group_buttons: function(group, button_label, action, visible_on_groups) {
            var self = this;
            if (visible_on_groups.length < 1 || visible_on_groups.indexOf(group.value) != -1) {
                var Objects = new instance.web.Model(this.fields_view.model);
                var kanban_dropdown = group.$el.find('.oe_kanban_group_dropdown');
              
                kanban_dropdown = jQuery(kanban_dropdown);
                kanban_dropdown.append('<li><a href="#">'+button_label+'</a></li>');
                
                kanban_dropdown.on('click', function() {
                    Objects.call(action, [group.value]).then(function (result) {
                        self.do_reload()
                    });
                });
            }
        },
    });
}