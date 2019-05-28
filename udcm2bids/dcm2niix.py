#----------------------------------------------------------------------------------------
#
#   Project - udcm2bids
#   Description:
#       A python processing package to convert UIH DICOM into bids format
#   File Name:    dcm2niix.py
#   Purpose:
#       to convert UIH specific dicom storage into bids format
#   Author: hui.liu02@united-imaging.com
#   Created 2019-04-19
#----------------------------------------------------------------------------------------

import os
import sys

_dcm2niix_root = os.path.dirname(__file__)
dcm2niix = ''
if sys.platform == 'win32':
    dcm2niix = os.path.join(_dcm2niix_root, 'exe', 'dcm2niix.exe')
elif sys.platform == 'darwin':
    dcm2niix = os.path.join(_dcm2niix_root, 'exe', 'dcm2niix_macos')
elif sys.platform == 'linux':
    dcm2niix = os.path.join(_dcm2niix_root, 'exe', 'dcm2niix_linux')
