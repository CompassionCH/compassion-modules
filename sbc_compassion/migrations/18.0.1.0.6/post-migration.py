from openupgradelib import openupgrade

# The B2S boxes are noupdate data: set the positions matching the templates.
TEXT_BOXES = {
    "sbc_compassion.b2s_l2_box_2": {"height": 46},
    "sbc_compassion.b2s_l3_box_1": {"height": 64.5},
    "sbc_compassion.b2s_l3_box_2": {"y_min": 7, "height": 79},
    "sbc_compassion.b2s_l4_box_1": {
        "x_min": 8.14,
        "y_min": 5,
        "width": 82.33,
        "height": 35.41,
    },
}


@openupgrade.migrate()
def migrate(env, version):
    for xmlid, vals in TEXT_BOXES.items():
        box = env.ref(xmlid, raise_if_not_found=False)
        if box:
            box.write(vals)
