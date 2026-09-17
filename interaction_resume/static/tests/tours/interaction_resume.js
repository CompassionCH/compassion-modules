import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

const CONTACT_URL_KEY = "interaction_resume.tour_contact_url";
if (/^\/odoo\/contacts\/\d+$/.test(location.pathname)) {
  sessionStorage.setItem(CONTACT_URL_KEY, location.pathname);
}
const CONTACT_URL = sessionStorage.getItem(CONTACT_URL_KEY) || "/odoo/contacts";

/** A date in the past, written the way the en_US user interface expects it. */
const pastDateTime = (daysAgo, hour, minute) =>
  luxon.DateTime.now()
    .minus({ days: daysAgo })
    .set({ hour, minute, second: 0, millisecond: 0 })
    .toFormat("MM/dd/yyyy HH:mm:ss");

/** The file the tour attaches to the interaction it logs. */
const ATTACHMENT_NAME = "letter-of-the-sponsor.txt";

/** The interaction resume is on screen and ready to be read. */
const RESUME_READY = ".o_list_view .o_list_buttons button.btn-refresh";

const isIncoming = (direction) =>
  direction === "in" || direction === "Incoming";
const arrowOf = (direction) => (isIncoming(direction) ? "down" : "up");
const colourOf = ({ direction, type }) => {
  if (type === "Mass") {
    return "text-muted";
  }
  if (isIncoming(direction)) {
    return "text-danger";
  }
  return ["Phone", "SMS"].includes(type) ? "text-info" : "text-success";
};

// Interactions logged by hand from the "Log interaction" action. Together they
// cover both directions, a plain type and a free type, and three send modes.
const LETTER = {
  type: "Paper",
  direction: "Incoming",
  date: pastDateTime(3, 9, 15),
  subject: "Handwritten letter received at the office",
  body: "The sponsor wrote to us to ask for news of the sponsored child.",
  attachment: ATTACHMENT_NAME,
};
const LETTER_REWRITTEN = `${LETTER.body} They also asked for a photograph.`;
const ANSWER = {
  type: "Email",
  direction: "Outgoing",
  date: pastDateTime(2, 11, 30),
  subject: "Answer written about the sponsored child",
  body: "We answered the sponsor and told how the sponsored child is doing.",
};
const VISIT = {
  type: "Other",
  otherType: "Visit at the office",
  direction: "Incoming",
  date: pastDateTime(1, 16, 5),
  subject: "The sponsor came to visit us",
  body: "The sponsor came to the office and we handed over the child folder.",
};

const INCOMING_CALL = {
  type: "Phone",
  direction: "in",
  date: pastDateTime(4, 10, 0),
  subject: "The sponsor called about the payment date",
  body: "The sponsor asked to move the payment to the end of the month.",
};
const OUTGOING_CALL = {
  type: "Phone",
  direction: "out",
  date: pastDateTime(2, 15, 45),
  subject: "We called the sponsor back about the payment date",
  body: "We confirmed the payment is now taken on the 25th of each month.",
};

// Communications generated for the contact and sent from their form.
const EMAIL_COMMUNICATION = {
  type: "Email",
  sendMode: "By e-mail",
  direction: "Outgoing",
  subject: "Confirmation of the new payment date",
  body: "Dear sponsor, your payment is now taken on the 25th of each month.",
};
const PRINTED_COMMUNICATION = {
  type: "Paper",
  sendMode: "Print report",
  direction: "Outgoing",
  subject: "Yearly news of the sponsored child",
  body: "Dear sponsor, here are the yearly news of the child you support.",
};

/** Goes back to the contact the tour was started on. */
const goToContact = () => [
  stepUtils.goToUrl(CONTACT_URL),
  {
    content: "The form of the contact is displayed",
    trigger: ".o_form_view button[name=open_interaction]",
  },
];

/** Picks an entry of the cog menu of the contact. */
const runContactAction = (label) => [
  {
    content: "Open the action menu of the contact",
    trigger: ".o_form_view .o_cp_action_menus i.fa-cog",
    run: "click",
  },
  {
    content: `Pick "${label}" in the action menu`,
    trigger: `.o-dropdown--menu span:contains("${label}")`,
    run: "click",
  },
];

/** Logs one interaction through the "Log interaction" wizard. */
const logInteraction = (interaction) => [
  ...runContactAction("Log interaction"),
  {
    content: "The wizard that logs an interaction is open",
    trigger: ".modal div[name=communication_type] select",
  },
  {
    content: `The interaction was a ${interaction.type} one`,
    trigger: ".modal div[name=communication_type] select",
    run: `selectByLabel ${interaction.type}`,
  },
  ...(interaction.otherType
    ? [
        {
          content: "Describe what kind of interaction it was",
          trigger: ".modal div[name=other_type] input",
          run: `edit ${interaction.otherType}`,
        },
      ]
    : []),
  {
    content: `The interaction was ${interaction.direction}`,
    trigger: ".modal div[name=direction] select",
    run: `selectByLabel ${interaction.direction}`,
  },
  {
    content: "Change the date and the time of the interaction",
    trigger: ".modal div[name=date] input",
    run: `edit ${interaction.date}`,
  },
  {
    content: "Write the subject of the interaction",
    trigger: ".modal div[name=subject] input",
    run: `edit ${interaction.subject}`,
  },
  {
    content: "Focus the text of the interaction",
    trigger: ".modal div[name=body] .odoo-editor-editable",
    run: "click",
  },
  {
    content: "Write down what was exchanged with the sponsor",
    trigger: ".modal div[name=body] .odoo-editor-editable",
    run: `editor ${interaction.body}`,
  },
  ...(interaction.attachment
    ? [
        {
          content: "Attach the scan of the letter to the interaction",
          trigger: ".modal .oe_fileupload .o_file_input_trigger",
          async run() {
            // The file input the widget uploads through is hidden, so a tour
            // cannot target it: reach it from the button next to it.
            const input = this.anchor
              .closest(".o_file_input")
              .querySelector("input.o_input_file");
            const file = new File(
              ["Scan of the letter the sponsor sent us."],
              interaction.attachment,
              { type: "text/plain" },
            );
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            input.files = dataTransfer.files;
            input.dispatchEvent(new Event("change", { bubbles: true }));
          },
        },
        {
          content: "The file is attached to the interaction",
          trigger: `.modal .o_attachment:contains("${interaction.attachment}")`,
        },
      ]
    : []),
  {
    content: "Log the interaction",
    trigger: ".modal button[name=log_interaction]",
    run: "click",
  },
  {
    content: "The wizard is closed and the contact is displayed again",
    trigger:
      "body:not(:has(.modal)) .o_form_view button[name=open_interaction]",
  },
];

/** Logs one phone call through the "Log your call" action. */
const logCall = (call) => [
  ...runContactAction("Log your call"),
  {
    content: "The form that logs a call is open on a call that was held",
    trigger:
      ".modal .o_statusbar_status button.o_arrow_button_current:contains(Held)",
  },
  {
    content: "Write the subject of the call",
    trigger: ".modal div[name=name] input",
    run: `edit ${call.subject}`,
  },
  {
    content: "Change the date and the time of the call",
    trigger: ".modal div[name=date] input",
    run: `edit ${call.date}`,
  },
  {
    content: `The call was ${call.direction === "in" ? "received" : "made"}`,
    trigger: `.modal div[name=direction] input[data-value=${call.direction}]`,
    run: "click",
  },
  {
    content: "Write down what was said during the call",
    trigger: ".modal div[name=description] textarea",
    run: `edit ${call.body}`,
  },
  {
    content: "Save the call",
    trigger: ".modal-footer .o_form_button_save",
    run: "click",
  },
  {
    content: "The dialog is closed and the contact is displayed again",
    trigger:
      "body:not(:has(.modal)) .o_form_view button[name=open_interaction]",
  },
];

/** Opens the interaction resume from the form of the contact. */
const openResume = () => [
  stepUtils.autoExpandMoreButtons(),
  {
    content: "Open the interaction resume of the contact",
    trigger: ".o_form_view button[name=open_interaction]",
    run: "click",
  },
  {
    content: "The interaction resume is displayed",
    trigger: RESUME_READY,
  },
];

/** Asks the interaction resume to fetch the interactions again. */
const refreshResume = () => [
  {
    content: "Refresh the interaction resume",
    trigger: RESUME_READY,
    run: "click",
  },
  {
    content: "The interaction resume is displayed again",
    trigger: ".o_list_view .o_data_row",
  },
];

/** Leaves whatever was opened from the resume and comes back to it. */
const backToResume = () => [
  {
    content: "Go back to the interaction resume",
    trigger: ".o_control_panel .breadcrumb-item.o_back_button",
    run: "click",
  },
  {
    content: "The interaction resume is displayed again",
    trigger: RESUME_READY,
  },
];

/**
 * Checks that one interaction is listed, that its colour and its arrow tell
 * which way it went, and that its text can be read on its own form.
 */
const checkInResume = (interaction) => [
  {
    content: `"${interaction.subject}" is listed in the interaction resume`,
    trigger: `.o_data_row:contains("${interaction.subject}")`,
  },
  {
    content: `Its colour says the interaction was ${interaction.direction}`,
    trigger:
      `tr.o_data_row.${colourOf(interaction)}` +
      `:contains("${interaction.subject}")`,
  },
  {
    content: `Its arrow says the interaction was ${interaction.direction}`,
    trigger:
      `.o_data_row:contains("${interaction.subject}") ` +
      `button[name=${isIncoming(interaction.direction) ? "in" : "out"}] ` +
      `.fa-arrow-${arrowOf(interaction.direction)}`,
  },
  {
    content: "Open the interaction",
    trigger: `.o_data_row:contains("${interaction.subject}") td[name=subject]`,
    run: "click",
  },
  {
    content: "The interaction carries the subject it was logged with",
    trigger: `.o_form_view div[name=subject]:contains("${interaction.subject}")`,
  },
  {
    content: "The text of the interaction can be read",
    trigger: `.o_form_view div[name=body]:contains("${interaction.body}")`,
  },
  ...backToResume(),
];

const checkAttachmentInResume = (withFile, withoutFile) => [
  {
    content: `The resume shows that "${withFile.subject}" carries a file`,
    trigger: `.o_data_row:contains("${withFile.subject}") button .fa-paperclip`,
  },
  ...withoutFile.map((interaction) => ({
    content: `The resume shows no file on "${interaction.subject}"`,
    trigger:
      `.o_data_row:contains("${interaction.subject}")` +
      ":not(:has(.fa-paperclip))",
  })),
];

/**
 * Rewrites the text of an interaction from the resume and comes back to it.
 * An entry of the resume is the record it was built from, so it has to be
 * still there afterwards, carrying what was just written.
 */
const rewriteFromResume = (interaction, text) => [
  {
    content: `Open the entry of "${interaction.subject}"`,
    trigger: `.o_data_row:contains("${interaction.subject}") td[name=subject]`,
    run: "click",
  },
  {
    content: "Open the interaction the entry was built from",
    trigger: ".o_form_view button[name=open_related_action]",
    run: "click",
  },
  {
    content: "The interaction that was logged is displayed",
    trigger: `.o_form_view div[name=subject] input:value("${interaction.subject}")`,
  },
  {
    content: "Focus the text of the interaction",
    trigger: ".o_form_view div[name=body] .odoo-editor-editable",
    run: "click",
  },
  {
    content: "Write down what was left out the first time",
    trigger: ".o_form_view div[name=body] .odoo-editor-editable",
    run: `editor ${text}`,
  },
  ...stepUtils.saveForm(),
  {
    content: "Go back to the entry of the resume",
    trigger: ".o_control_panel .breadcrumb-item.o_back_button",
    run: "click",
  },
  {
    content: "The entry is still there, and carries what was just written",
    trigger: `.o_form_view div[name=body]:contains("${text}")`,
  },
  ...backToResume(),
];

/** Checks that the chatter of the contact holds no note about an interaction. */
const checkNotLogged = (interactions) => [
  ...goToContact(),
  {
    content: "The messages of the contact are displayed",
    trigger: ".o-mail-Chatter .o-mail-Thread",
  },
  ...interactions.map((interaction) => ({
    content: `No note was left about "${interaction.subject}"`,
    trigger: `.o-mail-Thread:not(:has(.o-mail-Message:contains("${interaction.subject}")))`,
  })),
];

/**
 * Creates a communication for the contact and sends it. The communications of
 * the contact are reached from their form, which opens the very same creation
 * form as the Communications menu does.
 */
const sendCommunication = (communication) => [
  ...goToContact(),
  stepUtils.autoExpandMoreButtons(),
  {
    content: "Open the communications of the contact",
    trigger: ".o_form_view button.oe_stat_button:contains(Communications)",
    run: "click",
  },
  {
    content: "Create a new communication",
    trigger: ".o_control_panel_main_buttons .o_list_button_add",
    run: "click",
  },
  {
    content: "The communication is addressed to the contact",
    trigger: ".o_form_view div[name=partner_id] input:not(:value(''))",
  },
  {
    content: `The communication goes out as "${communication.sendMode}"`,
    trigger: ".o_form_view div[name=send_mode] select",
    run: `selectByLabel ${communication.sendMode}`,
  },
  ...stepUtils.saveForm(),
  {
    content: "Write the subject of the communication",
    trigger: ".o_form_view div[name=subject] input",
    run: `edit ${communication.subject}`,
  },
  {
    content: "Focus the text of the communication",
    trigger: ".o_form_view div[name=body_html] .odoo-editor-editable",
    run: "click",
  },
  {
    content: "Write the text of the communication",
    trigger: ".o_form_view div[name=body_html] .odoo-editor-editable",
    run: `editor ${communication.body}`,
  },
  ...stepUtils.saveForm(),
  {
    content: "Send the communication",
    trigger: ".o_form_view .o_form_statusbar button[name=send]:visible",
    run: "click",
  },
];

registry.category("web_tour.tours").add("interaction_resume_log_interaction", {
  steps: () => [
    ...logInteraction(LETTER),
    ...logInteraction(ANSWER),
    ...logInteraction(VISIT),
    ...openResume(),
    ...checkInResume(LETTER),
    ...checkInResume(ANSWER),
    ...checkInResume(VISIT),
    ...checkAttachmentInResume(LETTER, [ANSWER, VISIT]),
    ...refreshResume(),
    ...checkInResume(LETTER),
    ...checkInResume(ANSWER),
    ...checkInResume(VISIT),
    ...checkAttachmentInResume(LETTER, [ANSWER, VISIT]),
    // Editing an interaction must not take the resume down with it.
    ...rewriteFromResume(LETTER, LETTER_REWRITTEN),
    ...checkNotLogged([LETTER, ANSWER, VISIT]),
  ],
});

registry.category("web_tour.tours").add("interaction_resume_log_call", {
  steps: () => [
    ...logCall(INCOMING_CALL),
    ...logCall(OUTGOING_CALL),
    ...openResume(),
    ...refreshResume(),
    ...checkInResume(INCOMING_CALL),
    ...checkInResume(OUTGOING_CALL),
    ...checkNotLogged([INCOMING_CALL, OUTGOING_CALL]),
  ],
});

registry.category("web_tour.tours").add("interaction_resume_communication", {
  steps: () => [
    ...sendCommunication(EMAIL_COMMUNICATION),
    {
      content: "The communication was sent by e-mail",
      trigger:
        `.o_data_row:contains("${EMAIL_COMMUNICATION.subject}") ` +
        "td[name=state]:contains(Done)",
    },
    ...goToContact(),
    ...openResume(),
    ...checkInResume(EMAIL_COMMUNICATION),
    ...sendCommunication(PRINTED_COMMUNICATION),
    {
      content: "The letter was rendered to a PDF instead of a printer",
      trigger: ".modal div[name=letters_data] a.o_form_uri",
    },
    {
      content: "Close the dialog without throwing the PDF away",
      trigger: ".modal-footer button:contains('Close and keep data')",
      run: "click",
    },
    ...goToContact(),
    ...openResume(),
    ...checkInResume(PRINTED_COMMUNICATION),
  ],
});
