/**
 * This is the extension of the file:
 * bin/addons/web_calendar/static/src/js/web_calendar.js
 *
 * The aim is to override the function "quick_add" in order to have
 * more than a single field 'name' in the quick create popup.
 */
openerp.crm_compassion = function (instance) {

    instance.web.crm_compassion = instance.web.crm_compassion || {};
    instance.web_calendar.QuickCreate = instance.web_calendar.QuickCreate.extend({

        /**
         * Generate and modify html at the moment we click on a day of the
         * calendar. This is the function that you need to
         * modify if you want to change the quickcreate popup.
         */
        start: function() {
            this._super();

            if (this.getParent().model !== "crm.event.compassion"){
                return;
            }

            //rename the original label 'Event summary:' to 'Event name:'
            $( "label:contains('Event summary:')" ).text("Event name:");

            // create a drop-down option list
            var options = {
                '':'',
                'stand':'Stand',
                'concert':'Concert',
                'presentation':'Presentation',
                'meeting':'Meeting',
                'sport':'Sport event',
                'tour':'Sponsor tour'
            };
            this.append_option_input_jquery("div_crm_event_compassion", "type", options, "Type:");

            // create two other input for fields number_allocate_children
            // and planned_sponsorships.
            this.append_input_jquery("div_crm_event_compassion", 'number_allocate_children', 'Number of children to allocate:');
            this.append_input_jquery("div_crm_event_compassion", 'planned_sponsorships', 'Expected sponsorships:');

            //The following correspond to the html code we want to generate:

            // <label id="type_label_id" for='type' class='control-label'>Type:</label>
            // <select id="type_select_id" name='type' class="form-control myInputs">
            //     <option value=""></option>
            //     <option value="stand">Stand</option>
            //     <option value="concert">Concert</option>
            //     <option value="presentation">Presentation</option>
            //     <option value="meeting">Meeting</option>
            //     <option value="sport">Sport event</option>
            //     <option value="tour">Sponsor tour</option>
            // </select>
            //
            // <label id="number_allocate_children_label_id" for='number_allocate_children' class='control-label'>Number of children to allocate:</label>
            // <input id="number_allocate_children_input_id" name='number_allocate_children' class="form-control myInputs"/>
            //
            // <label id="planned_sponsorships_label_id" for='planned_sponsorships' class='control-label'>Expected sponsorships:</label>
            // <input id="planned_sponsorships_input_id" name='planned_sponsorships' class="form-control myInputs"/>
        },

        /**
         * Generate an html tag with its attribute and text, and return
         * the generated tag_id. The tag_id can be used later to append new
         * tags to this one.
         *
         * @param tag: 'label', 'input', 'div', 'span' or whatever...
         * @param attributes: associative array under the form
         *          {attribute:value, ...}
         * @param master_id: id of the tag to which we want to append the
         *          current tag
         * @param var_name: name of the affected field in the record
         * @param text: inner text of the tag if needed
         * @returns {string}: return the tag_id
         */
        new_tag: function(tag, attributes, master_id, var_name, text){
            text = text || '';
            var tag_id = var_name+"_" + tag + "_id";
            var command = '<'+tag+' id="' + tag_id +'"></'+tag+'>';
            $("#"+master_id).append(command);
            $("#"+tag_id).attr(attributes);
            $("#"+tag_id).text(text);
            return tag_id;
        },


        /**
         * Add a simple input field (text box) with its label
         * @param master_id: id of the tag to which we want to append
         *          the input text box
         * @param var_name: name of the affected field in the record
         * @param text: Description of the field (label)
         */
        append_input_jquery: function(master_id, var_name, text){
            // <label id="VAR_NAME_label_id" for='VAR_NAME' class='control-label myInputs'>TEXT:</label>
            this.new_tag('label', {"for":var_name, "class":"control-label"}, master_id, var_name, text);

            // <input id="VAR_NAME_input_id" name='VAR_NAME' class="form-control myInputs"/>
            this.new_tag('input', {"name":var_name,  "class": "form-control myInputs"}, master_id, var_name);
        },


        /**
         * Add a new drop-down list with different options.
         * @param master_id: id of the tag to which we want to append
         *          the drop-down list
         * @param var_name: name of the affected field in the record
         * @param options: associative array {option_value: option_name,...}
         * @param text: Description of the field (label)
         */
        append_option_input_jquery: function(master_id, var_name, options, text){
            var option_values = [];
            var option_txt = [];
            $.each(options, function(val, txt){
                option_values.push(val);
                option_txt.push(txt);
            });

            // <label id="VAR_NAME_label_id" for='VAR_NAME' class='control-label myInputs'>TEXT:</label>
            this.new_tag('label', {
                "for":var_name,
                "class":"control-label"
            }, master_id, var_name, text);

            //<select id="VAR_NAME_select_id" name='VAR_NAME' class="form-control myInputs">
            var select_id = this.new_tag('select', {
                "name":var_name,
                "class":"form-control myInputs",
            }, master_id, var_name);

            for (var i = 0; i < option_txt.length; i++){
                // <option id="OPTION_VALUES[i]_option_id" value="OPTION_VALUES[i]">OPTION_TXT[i]</option>
                this.new_tag('option', {"value":option_values[i]}, select_id, option_values[i], option_txt[i]);
            }
        },

        /**
         * Create and return an associative array
         *      vals = { field0:value0, field1:value1, ...}
         * @param inputs
         * @returns {*}
         */
        getVals: function(inputs){
            var vals = [];
            for (var i = 0; i < inputs.length; i++){
                var field = inputs[i].name;
                var value = inputs[i].value;

                // All fields are mandatory, so we refuse to create the
                // record if one information is missing
                if (value === ""){
                    window.alert("You have to fill all the fields.");
                    return false
                }
                vals[field] = value;
            }
            return vals;
        },

        /**
         * Gathers data from the quick create dialog and launch
         * quick_create(data) method.
         */
        quick_add: function() {

            // create a dictionary (called associative array in javascript)
            // with the values stored in input
            var vals_1 = this.getVals(this.$input); // original input field
            if (vals_1 === false){return false;}

            var vals_2 = this.getVals(jQuery('.myInputs')); // our extended inputs
            if (vals_2 === false){return false;}

            var vals = $.extend({},vals_1, vals_2); //merge the two arrays

            return this.quick_create(vals).always(function() { return true; });
        },

    });

    /*
        Quick add a survey for R4 requests !
     */
    instance.web.WebClient.include({
		show_application: function () {
			this._super();
            jQuery.ajax({
                url: "https://jira.compassion.ch/s/71d9b4a48de5d393d2032f16e6cc03e5-T/fr_FR-fzisf3/71004/b6b48b2829824b869586ac216d119363/2.0.11/_/download/batch/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector-embededjs/com.atlassian.jira.collector.plugin.jira-issue-collector-plugin:issuecollector-embededjs.js?locale=fr-FR&collectorId=39e061fc",
                type: "get",
                cache: true,
                dataType: "script",
            });
            // Copy phone button and use it for opening JIRA tracker
            self = this;
            window.setTimeout(function () {
                self.$(".oe_topbar_open_caller").after(self.$(".oe_topbar_open_caller").clone());
                var mySelector = self.$(".oe_topbar_open_caller :last");
                mySelector.removeClass(".oe_topbar_open_caller").addClass(".oe_topbar_open_jira");
                mySelector.attr("title", "Submit Change Request");
                mySelector.find("#asterisk-open-caller").attr("id", "jira-open").removeClass("fa-phone").addClass("fa-file");

                window.ATL_JQ_PAGE_PROPS = {
                    "triggerFunction": function (showCollectorDialog) {
                        //Requires that jQuery is available!
                        jQuery("#jira-open").click(function (e) {
                            console.log('Click!!!');
                            e.preventDefault();
                            showCollectorDialog();
                        });
                    }
                };
            }, 2000);
		}
	});

};
