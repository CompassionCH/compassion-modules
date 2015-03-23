openerp.sponsorship_tracking = function (instance) { 
    instance.web.sponsorship_tracking = instance.web.sponsorship_tracking || {};
    var Contracts = new instance.web.Model("recurring.contract");
    
    instance.web.views.add('kanban', 'instance.web_kanban.SDSTrackingKanban');
    instance.web_kanban.SDSTrackingKanban = instance.web_kanban.KanbanView.extend({
        template: "KanbanView",
        on_record_moved: function(record, old_group, old_index, new_group, new_index) {
            if (this.__parentedParent.process_model != 'recurring.contract') {
                return this._super(record, old_group, old_index, new_group, new_index);
            }
            if (old_group === new_group) {
                return this._super(record, old_group, old_index, new_group, new_index);
            }
            var self = this;
            Contracts.call('state_transition_from_kanban', [old_group.value, new_group.value, record.id]).done(function (res) {
                if (!res) {
                    record.$el.remove();
                    new_group.records.splice(new_index, 1);
                    old_group.records.splice(old_index, 1);
                    $(old_group.records[old_index].$el).before(record.$el);
                    old_group.records.splice(old_index, 0, record);
                    record.group = old_group;

                    record.do_reload();
                }
            });
        },
    });
}