
########################################################################
#
#  zxing.py -- a quick and dirty wrapper for zxing for python
#
#  this allows you to send images and get back data from the ZXing
#  library:  http://code.google.com/p/zxing/
#
#  by default, it will expect to be run from the zxing source code directory
#  otherwise you must specify the location as a parameter to the constructor
#
#  original version on github.com/oostendo/python-zxing

__version__ = '0.4'
import subprocess, re, os

class BarCodeTool():
  """
  This class needs to use the method decode/encode in order to do something
  At the initialization, the directories names are set up and the non-changing
  (between two utilization) part is written
  """
  location = ""
  command = "java"
  libs = ["javase.jar", "core.jar", "jcommander.jar", "jai-imageio-core.jar"]
  args = ["-cp", "LIBS"]
  args_de = ["com.google.zxing.client.j2se.CommandLineRunner"]
  args_en = ["com.google.zxing.client.j2se.CommandLineEncoder"]

  def __init__(self, loc=""):
    if not len(loc):
      if ("HOME" in os.environ):
        loc = os.environ["HOME"] + "/.libZxing"
      else:
        loc = ".."

    self.location = loc

  def decode(self, files, try_harder = False,qr_only=True):
    """
    Decodes a/some file/s
    :param string files: Name of the files to decode
    :param bool try_harder: Spend more time to find a barcode (if needed)
    :param bool qr_only: Only check for QR code or not
    :returns: Information about the barcode
    :rtype: BarCode
    """    
    cmd = [self.command]
    cmd += self.args[:] #copy arg values
    cmd += self.args_de


    # send one file, or multiple files in a list
    SINGLE_FILE = False
    if type(files) != type(list()):
      cmd.append(files)
      SINGLE_FILE = True
    else:
      cmd += files

    if try_harder:
      cmd.append("--try_harder")
    if qr_only:
      cmd.append("--possible_formats")
      cmd.append("QR_CODE")

    libraries = [self.location + "/" + l for l in self.libs]

    cmd = [ c if c != "LIBS" else os.pathsep.join(libraries) for c in cmd ]

    (stdout, stderr) = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        universal_newlines=True).communicate()
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
    Create a Barcode (written in PNG format [the library can accepts JPG,GIF 
    as a paramter to the command line])
    :param string file_: File name where to write the barcode
    :param string text: Text to encode
    :param string code_format: Type of barcode (see github, zxing project)
    :param int width: Width of the ouput image
    :param int height: Height of the output image
    """

    cmd = [self.command]
    cmd += self.args[:] #copy arg values
    cmd += self.args_en
    libraries = [self.location + "/" + l for l in self.libs]

    cmd = [ c if c != "LIBS" else os.pathsep.join(libraries) for c in cmd ]

    cmd.append(text)
    if width != None:
      cmd.append("--width")
      cmd.apppend(width)
    if height != None:
      cmd.append("--height")
      cmd.append(height)
    if code_format != None:
      cmd.append("--barcode_format")
      cmd.append(code_format)
    if errorcorrection != None:
      cmd.append("--error_correction")
      cmd.append(errorcorrection)

    cmd.append("--output")
    cmd.append(file_)
    (stdout, stderr) = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        universal_newlines=True).communicate()

class BarCode:
  """
  Class containing all the information about the codebars
  """
  format = ""
  points = []
  data = ""
  raw = ""

  def __init__(self, zxing_output):
    lines = zxing_output.split("\n")
    raw_block = False
    parsed_block = False
    point_block = False

    self.points = []
    for l in lines:
      m = re.search("format:\s([^,]+)", l)
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

      if parsed_block and not re.match("Found\s\d\sresult\spoints", l):
        self.data += l + "\n"
        continue

      if parsed_block and re.match("Found\s\d\sresult\spoints", l):
        parsed_block = False
        point_block = True
        continue

      if point_block:
        m = re.search("Point\s(\d+):\s\(([\d\.]+),([\d\.]+)\)", l)
        if (m):
          self.points.append((float(m.group(2)), float(m.group(3))))

    return


if __name__ == "__main__":
  print("ZXing module")
