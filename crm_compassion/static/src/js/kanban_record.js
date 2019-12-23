odoo.define('crm_compassion_web_kanban.Record', function (require) {
    "use strict";

    var KanbanRecord = require('web_kanban.Record');

    // Overriding 'kanban_getcolor' in web_kanban/static/js/kanban_record.js
    var KanbanRecordUpdated = KanbanRecord.include({
        kanban_getcolor: function (variable) {
            if (typeof variable === 'number') {
                return Math.round(variable) % 20;
            }
            if (typeof variable === 'string') {
                var index = 0;
                for (var i=0; i<variable.length; i++) {
                    index += variable.charCodeAt(i);
                }
                return index % 20;
            }
            return 0;
        },
    });

    return KanbanRecordUpdated;
});
