##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Tarabbia <jtarabbia@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
"""
Define the class CheckboxReader that read a checkbox (the input image
should contains more or less only the box).
"""
import logging

_logger = logging.getLogger(__name__)
try:
    from boxdetect.pipelines import get_checkboxes
    from boxdetect import config

    # Uncomment for testing and seeing the detection results (needs matplotlib)
    # from boxdetect import config
    # from boxdetect.pipelines import get_boxes
    # import matplotlib.pyplot as plt

except ImportError:
    _logger.warning("Please install boxdetect on your system to use SBC module")


def find_languages_area(env, filename):
    try:
        cfg = config.PipelinesConfig()

        # important to adjust these values to match the size of boxes on your image
        cfg.width_range = (50, 60)
        cfg.height_range = (50, 60)

        # the more scaling factors the more accurate the results but also it takes
        # more time to processing too small scaling factor may cause false positives
        # too big scaling factor will take a lot of processing time
        cfg.scaling_factors = [0.5]

        # w/h ratio range for boxes/rectangles filtering
        cfg.wh_ratio_range = (0.5, 1.7)

        # group_size_range starting from 2 will skip all the groups
        # with a single box detected inside (like checkboxes)
        cfg.group_size_range = (2, 100)

        # num of iterations when running dilation tranformation (to engance the image)
        cfg.dilation_iterations = 0

        # Uncomment to plot the results in pycharm using matplotlib
        # rects, grouping_rects, image, output_image = get_boxes(
        #     filename, cfg=cfg, plot=False)
        # print(grouping_rects)

        # plt.figure(figsize=(20, 20))
        # plt.imshow(output_image)
        # plt.show()

        # limit down the grouping algorithm to just singular boxes (e.g. checkboxes)
        cfg.group_size_range = (1, 1)

        checkboxes = get_checkboxes(
            filename, cfg=cfg, px_threshold=0.1, plot=False, verbose=True)

        # print("Output object type: ", type(checkboxes))
        lang = env['res.lang.compassion']
        for checkbox in checkboxes:
            # Uncomment to plot the results
            # print("Checkbox bounding rectangle (x,y,width,height): ", checkbox[0])
            # print("Result of `contains_pixels` for the checkbox: ", checkbox[1])
            # print("Display the cropout of checkbox:")
            # plt.figure(figsize=(1, 1))
            # plt.imshow(checkbox[2])
            # plt.show()

            if checkbox[1] and 1800 < checkbox[0][0] < 2000 and \
                    250 < checkbox[0][1] < 280:
                lang = env['res.lang.compassion'].search([
                    ('name', '=', 'Spanish')])
            elif checkbox[1] and 1100 < checkbox[0][0] < 1300 and \
                    80 < checkbox[0][1] < 110:
                lang = env['res.lang.compassion'].search([
                    ('name', '=', 'French')])
            elif checkbox[1] and 1800 < checkbox[0][0] < 2000 and \
                    80 < checkbox[0][1] < 130:
                lang = env['res.lang.compassion'].search([
                    ('name', '=', 'English')])
            elif checkbox[1] and 1100 < checkbox[0][0] < 1300 and \
                    240 < checkbox[0][1] < 270:
                lang = env['res.lang.compassion'].search([
                    ('name', '=', 'German')])
            elif checkbox[1] and 1100 < checkbox[0][0] < 1300 and \
                    390 < checkbox[0][1] < 430:
                lang = env['res.lang.compassion'].search([
                    ('name', '=', 'Italian')])

        return lang

    except:
        _logger.warning("Error during checkbox detection", exc_info=True)
        return env['res.lang.compassion']
