#----------------------------------------------------------------------------------------
#
#   Project - udcm2bids
#   Description:
#       A python processing package to convert UIH DICOM into bids format
#   File Name:    udcmview.py
#   Purpose:
#       to convert UIH specific dicom storage into bids format
#   Author: hui.liu02@united-imaging.com
#   Created 2019-05-31
#----------------------------------------------------------------------------------------

import os
import difflib
import pydicom
import shutil

import pandas as pd

from glob import glob

#----------------------------------------------------------------------------------------
#
def dump_series2json(dcm_root, series_file_pattern='00000001.dcm'):
    """
    :param dcm_root:
    :param series_file_pattern:
    :return:
    """
    if not os.path.exists(dcm_root): return {}
    series = {'PatientName':[],
              'PatientID':[],
              'StudyDate':[],
              'AcquisitionDateTime':[],
              'SeriesDescription':[],
              'NumberofSlices':[],
              'Load':[]}
    for subdir, _, files in os.walk(dcm_root):
        if len(files) <= 0: continue
        if files[0] != series_file_pattern: continue
        print('working on %s'%(subdir))
        ds = pydicom.read_file(os.path.join(subdir, files[0]))
        try:
            series['PatientName'].append(ds.PatientName)
            series['PatientID'].append(ds.PatientID)
            series['StudyDate'].append(ds.StudyDate)
            series['AcquisitionDateTime'].append(ds.AcquisitionDateTime)
            series['SeriesDescription'].append(ds.SeriesDescription)
            series['NumberofSlices'].append(len(files))
            series['Load'].append(False)
        except:
            pass
    return series
#----------------------------------------------------------------------------------------
#
def dump_series2xlsx(dcm_root, xlsx_file):
    """
    :param dcm_root:
    :param xlsx_file:
    :return:
    """
    series = dump_series2json(dcm_root)
    if os.path.exists(xlsx_file):
        df_0 = pd.read_excel(xlsx_file)
        df_1 = pd.DataFrame(series)
        df = pd.concat([df_0, df_1], axis=0)
    else:
        df = pd.DataFrame(series)
    df.to_excel(xlsx_file)
    return
#----------------------------------------------------------------------------------------
#
def cp_series(dcm_root, target_root, xlsx_file):
    """
    :param dcm_root:
    :param target_root:
    :param xlsx_file:
    :return:
    """
    if not os.path.exists(dcm_root): return
    if not os.path.exists(xlsx_file): return
    if not os.path.exists(target_root): os.makedirs(target_root)
    series_tags = pd.read_excel(xlsx_file)
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
            series_folder = os.path.join(target_root, patient_name, study_date, series_id + '_' + series_description)
            if not os.path.exists(series_folder): os.makedirs(series_folder)
            shutil.copyfile(os.path.join(subdir, file), os.path.join(series_folder, file))
    return
#----------------------------------------------------------------------------------------
#
def diff_dcm_files(dcm_file_0, dcm_file_1):
    """
    :param dcm_file_0:
    :param dcm_file_1:
    :return:
    """
    ds_0 = pydicom.read_file(dcm_file_0, force=True)
    ds_1 = pydicom.read_file(dcm_file_1, force=True)
    dss = tuple([ds_0, ds_1])
    rep = []
    for ds in dss:
        lines = str(ds).split("\n")
        lines = [line + "\n" for line in lines]  # add the newline to end
        rep.append(lines)
    diff = difflib.Differ()
    for line in diff.compare(rep[0], rep[1]):
        if line[0] != "?": print(line)
    return

#----------------------------------------------------------------------------------------
#
# Test Purpose
#
#----------------------------------------------------------------------------------------
if __name__ == '__main__':
    dcm_root = '\\\\dataserver02\\PET-MR02\\11. 场地数据\\北京宣武医院'
    xlsx_file = 'D:\\xuanwu.xlsx'
    patient_dcm_roots = glob(os.path.join(dcm_root, '2019*'))
    for patient_dcm_root in patient_dcm_roots:
        dump_series2xlsx(dcm_root, xlsx_file)
