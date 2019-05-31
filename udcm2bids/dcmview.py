#----------------------------------------------------------------------------------------
#
#   Project - udcm2bids
#   Description:
#       A python processing package to convert UIH DICOM into bids format
#   File Name:    dcmview.py
#   Purpose:
#       to convert UIH specific dicom storage into bids format
#   Author: hui.liu02@united-imaging.com
#   Created 2019-05-31
#----------------------------------------------------------------------------------------

import os
import pydicom
import shutil

import pandas as pd

#----------------------------------------------------------------------------------------
#
def dump_series2json(dcm_root):
    """
    :param dcm_root:
    :return:
    """
    if not os.path.exists(dcm_root): return {}
    series = {'SeriesDescription':[], 'Load':[]}
    for subdir, _, files in os.walk(dcm_root):
        if len(files) <= 0: continue
        for file in files:
            ds = pydicom.read_file(os.path.join(subdir, file))
            if ds.SeriesDescription in series['SeriesDescription']: continue
            series['SeriesDescription'].append(ds.SeriesDescription)
            series['Load'].append(False)
    return series
#----------------------------------------------------------------------------------------
#
def cp_series(dcm_root, series_tag_xlsxfile, tar_root):
    """
    :param dcm_root:
    :param series_tag_xlsxfile:
    :param tar_root:
    :return:
    """
    if not os.path.exists(dcm_root): return
    if not os.path.exists(series_tag_xlsxfile): return
    if not os.path.exists(tar_root): os.makedirs(tar_root)
    series_tags = pd.read_excel(series_tag_xlsxfile)
    for subdir, _, files in os.walk(dcm_root):
        if len(files) <= 0: continue
        for file in files:
            ds = pydicom.read_file(os.path.join(subdir, file))
            load = series_tags[series_tags['SeriesDescription'] == str(ds.SeriesDescription)]['Load'].values[0]
            if not load: continue
            patient_name = str(ds.PatientName)
            study_date = str(ds.StudyDate)
            series_id = str(ds.SeriesNumber)
            series_description = str(ds.SeriesDescription)
            series_folder = os.path.join(tar_root, patient_name, study_date, series_id + '_' + series_description)
            if not os.path.exists(series_folder): os.makedirs(series_folder)
            shutil.copyfile(os.path.join(subdir, file), os.path.join(series_folder, file))
    return
#----------------------------------------------------------------------------------------
#
# Test Purpose
#
#----------------------------------------------------------------------------------------
if __name__ == '__main__':
    dcm_root = 'C:\\Users\\hui.liu02\\Desktop\\GABA\\gaba2'
    #series = dump_series2json(dcm_root)
    #df = pd.DataFrame(series)
    #df.to_excel('C:\\Users\\hui.liu02\\Desktop\\GABA\\gaba2.xlsx')
    #"""
    cp_series(dcm_root,
              'C:\\Users\\hui.liu02\\Desktop\\GABA\\gaba2.xlsx',
              'C:\\Users\\hui.liu02\\Desktop\\GABA\\gaba')
    #"""
