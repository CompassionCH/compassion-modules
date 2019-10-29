# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nate Oostendo <nate@oostendorp.net>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
# This file has been written by Nate Oostendo but edited inside compassion
# This header is done for travis and we are not claiming any right on his code
# (only the modifications).
"""
 zxing.py -- a quick and dirty wrapper for zxing for python

 this allows you to send images and get back data from the ZXing
 library:  http://code.google.com/p/zxing/

 by default, it will expect to be run from the zxing source code directory
 otherwise you must specify the location as a parameter to the constructor

 original version on github.com/oostendo/python-zxing
"""

import subprocess
import re
import os
__version__ = '0.5'


class BarCodeTool():
    """
    This class needs to use the method decode/encode in order to do something
    At the initialization, the directories names are set up and the
    non-changing (between two utilization) part is written
    """
    location = ""
    command = "java"
    libs = ["javase.jar", "core.jar", "jcommander.jar", "jai-imageio-core.jar"]
    args = ["-cp", "LIBS"]
    args_de = ["com.google.zxing.client.j2se.CommandLineRunner"]
    args_en = ["com.google.zxing.client.j2se.CommandLineEncoder"]

    ##########################################################################
    #                               INIT METHOD                              #
    ##########################################################################
    def __init__(self, loc=""):
        if not len(loc):
            if ("HOME" in os.environ):
                loc = os.environ["HOME"] + "/.libZxing"
            else:
                loc = ".."

        self.location = loc

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def scan_qrcode(self, data):
        qrdata = None

        decoder = BarCodeTool()
        result = decoder.decode(data)
        # map the resulting object to a dictionary compatible to our software
        if result:
            qrdata = {}
            qrdata["data"] = result.data.strip()
            qrdata["format"] = result.format
            qrdata["points"] = result.points
            qrdata["raw"] = result.raw.strip()
        return qrdata

    def decode(self, files, try_harder=True, qr_only=True, crop=None):
        """
        Decodes a/some file/s

        :param string files: Name of the files to decode
        :param bool try_harder: Spend more time to find a barcode (if needed)
        :param bool qr_only: Only check for QR code or not
        :param list crop: Use a subset of the picture [left,top,width,height]\
            (in pixels)
        :returns: Information about the barcode
        :rtype: BarCode
        """
        cmd = [self.command]
        cmd += self.args[:]  # copy arg values
        cmd += self.args_de

        # send one file, or multiple files in a list
        SINGLE_FILE = False
        if not isinstance(files, list):
            cmd.append(files)
            SINGLE_FILE = True
        else:
            cmd += files

        if try_harder:
            cmd.append("--try_harder")
        if qr_only:
            cmd.append("--possible_formats")
            cmd.append("QR_CODE")
            # cmd.append("--possibleFormats=QR_CODE")
        if crop is not None:
            cmd.append("--crop")
            for i in range(4):
                cmd.append(str(crop[i]))

        libraries = [self.location + "/" + l for l in self.libs]

        cmd = [c if c != "LIBS" else os.pathsep.join(libraries) for c in cmd]
        (stdout, stderr) = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, universal_newlines=True).communicate()
        codes = []
        file_results = stdout.split("\nfile:")
        for result in file_results:
            lines = stdout.split("\n")
            if re.search("No barcode found", lines[0]):
                codes.append(None)
                continue

            codes.append(BarCode(result))

        if SINGLE_FILE:
            return codes[0]
        else:
            return codes

    def encode(self, file_, text, code_format=None, width=None, height=None,
               errorcorrection=None):
        """
        Create a Barcode (written in PNG format [the library can accepts JPG,
        GIF as a paramter to the command line])

        :param string file_: File name where to write the barcode
        :param string text: Text to encode
        :param string code_format: Type of barcode (see github, zxing project)
        :param int width: Width of the ouput image
        :param int height: Height of the output image
        :param int errorcorrection: Correction level (QR code between 0 and 3)
        """

        cmd = [self.command]
        cmd += self.args[:]  # copy arg values
        cmd += self.args_en
        libraries = [self.location + "/" + l for l in self.libs]

        cmd = [c if c != "LIBS" else os.pathsep.join(libraries) for c in cmd]

        cmd.append(text)
        if width is not None:
            cmd.append("--width")
            cmd.append(str(width))
        if height is not None:
            cmd.append("--height")
            cmd.append(str(height))
        if code_format is not None:
            cmd.append("--barcode_format")
            cmd.append(code_format)
        if errorcorrection is not None:
            cmd.append("--error_correction_level")
            cmd.append(errorcorrection)

        cmd.append("--output")
        cmd.append(file_)

        (stdout, stderr) = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, universal_newlines=True).communicate()


class BarCode:
    """
    Class containing all the information about the codebars
    """
    format = ""
    points = []
    data = ""
    raw = ""

    ##########################################################################
    #                               INIT METHOD                              #
    ##########################################################################
    def __init__(self, zxing_output):
        lines = zxing_output.split("\n")
        raw_block = False
        parsed_block = False
        point_block = False

        self.points = []
        for l in lines:
            m = re.search(r"format:\s([^,]+)", l)
            if not raw_block and not parsed_block and not point_block and m:
                self.format = m.group(1)
                continue

            if (not raw_block and not parsed_block and not point_block and
                    l == "Raw result:"):
                raw_block = True
                continue

            if raw_block and l != "Parsed result:":
                self.raw += l + "\n"
                continue

            if raw_block and l == "Parsed result:":
                raw_block = False
                parsed_block = True
                continue

            if parsed_block and not re.match(r"Found\s\d\sresult\spoints", l):
                self.data += l + "\n"
                continue

            if parsed_block and re.match(r"Found\s\d\sresult\spoints", l):
                parsed_block = False
                point_block = True
                continue

            if point_block:
                m = re.search(r"Point\s(\d+):\s\(([\d\.]+),([\d\.]+)\)", l)
                if (m):
                    self.points.append((float(m.group(2)), float(m.group(3))))

        return
