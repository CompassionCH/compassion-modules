odoo.define("crm_compassion.KanbanRecord", function (require) {
  "use strict";
  const _t = require("web.core")._t;

  var KanbanRecord = require("web.KanbanRecord");
  var KANBAN_RECORD_COLORS = [
    _t("No color"),
    _t("Light red"),
    _t("Orange"),
    _t("Yellow"),
    _t("Light blue"),
    _t("Dark purple"),
    _t("Salmon pink"),
    _t("Medium blue"),
    _t("Dark blue"),
    _t("Fushia"),
    _t("Light green"),
    _t("Purple"),
    _t("Dark red"),
    _t("Blue"),
    _t("Red"),
    _t("Brown"),
    _t("Green"),
    _t("Light yellow"),
    _t("Beige"),
    _t("Pastel green"),
    _t("Tommy blue"),
    _t("Dark grey"),
    _t("Dark violet"),
    _t("Dark brown"),
    _t("Greyish blue"),
  ];
  var NB_KANBAN_RECORD_COLORS = KANBAN_RECORD_COLORS.length;

  // Overriding '_getColorID' in web/static/src/js/views/kanban/kanban_record.js to use our custom colors
  var KanbanRecordUpdated = KanbanRecord.include({
    _getColorID: function (variable) {
      // Same code as source but the global variables have changed.
      console.log("custom kanban color called");
      if (typeof variable === "number") {
        return Math.round(variable) % NB_KANBAN_RECORD_COLORS;
      }
      if (typeof variable === "string") {
        var index = 0;
        for (var i = 0; i < variable.length; i++) {
          index += variable.charCodeAt(i);
        }
        return index % NB_KANBAN_RECORD_COLORS;
      }
      return 0;
    },
  });

  return KanbanRecordUpdated;
});
