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
import re
import difflib
import pydicom
import shutil

import pandas as pd

from glob import glob
from pydicom.misc import is_dicom

#----------------------------------------------------------------------------------------
#
def dump_series2json(dcm_root, mode='one_per_dir', series_file_pattern='00000001.dcm'):
    """
    :param dcm_root:
    :param mode:        'one_per_dir'
    :param series_file_pattern:
    :return:
    """
    if not os.path.exists(dcm_root): return {}
    series = {'01_PatientName':[],
              '02_PatientID':[],
              '03_StudyDate':[],
              '04_AcquisitionDateTime':[],
              '05_SeriesDescription':[],
              '06_NumberofSlices':[],
              '07_Load':[],
              '08_SeriesRoot':[],
              '09_SeriesFiles':[]}
    for subdir, _, files in os.walk(dcm_root):
        if len(files) <= 0: continue
        print('working on %s' % (subdir))
        # find right patterned files
        re_pattern = series_file_pattern.replace('*', '.*')
        r_files = []
        if mode != 'one_per_dir': r_files = files
        else:
            for file in files: r_files += re.findall(re_pattern, file)
            r_files.sort()
            r_files = [r_files[0]]
        # iterate all found files
        pnames = []
        pids = []
        sdates = []
        sdecrps = []
        acqdatetimes = []
        subdirs = []
        slices = {}
        series_keys = []
        for file in r_files:
            dcm_file = os.path.join(subdir, file)
            if not is_dicom(dcm_file): continue
            ds = pydicom.read_file(dcm_file)
            if hasattr(ds, 'AcquisitionDate'): acqdate = str(ds.AcquisitionDate)
            else: acqdate = 'NA'
            if hasattr(ds, 'AcquisitionTime'): acqtime = str(ds.AcquisitionTime)
            else: acqtime = 'NA'
            if hasattr(ds, 'PatientName'): pname = str(ds.PatientName)
            else: pname = 'NA'
            if hasattr(ds, 'PatientID'): pid = str(ds.PatientID)
            else: pid = 'NA'
            if hasattr(ds, 'StudyDate'): sdate = str(ds.StudyDate)
            else: sdate = 'NA'
            if hasattr(ds, 'SeriesDescription'): sdecrp = str(ds.SeriesDescription)
            else: sdecrp = 'NA'
            series_key = str(sdecrp + subdir)
            if series_key not in series_keys:
                series_keys.append(series_key)
                slices[series_key] = []
                pnames.append(pname)
                pids.append(pid)
                sdates.append(sdate)
                sdecrps.append(sdecrp)
                acqdatetimes.append(acqdate + acqtime)
                subdirs.append(subdir)
            slices[series_key].append(file)
        # append to series
        series['01_PatientName'] += pnames
        series['02_PatientID'] += pids
        series['03_StudyDate'] += sdates
        series['04_AcquisitionDateTime'] += acqdatetimes
        series['05_SeriesDescription'] += sdecrps
        series['07_Load'] += [False] * len(pnames)
        series['08_SeriesRoot'] += subdirs
        for series_key in series_keys:
            series['06_NumberofSlices'].append(len(slices[series_key]))
            series['09_SeriesFiles'].append(slices[series_key])
    return series
#----------------------------------------------------------------------------------------
#
def dump_series2xlsx(dcm_root, xlsx_file, mode='one_per_dir', series_file_pattern='00000001.dcm'):
    """
    :param dcm_root:
    :param xlsx_file:
    :param mode:            'one_per_dir'
    :param series_file_pattern:
    :return:
    """
    series = dump_series2json(dcm_root, mode=mode, series_file_pattern=series_file_pattern)
    if os.path.exists(xlsx_file):
        df_0 = pd.read_excel(xlsx_file)
        df_1 = pd.DataFrame(series)
        df = pd.concat([df_0, df_1], axis=0, sort=True)
    else:
        df = pd.DataFrame(series)
    df.to_excel(xlsx_file)
    return
#----------------------------------------------------------------------------------------
#
def cp_series(xlsx_file, target_root):
    """
    :param xlsx_file:
    :param target_root:
    :return:
    """
    if not os.path.exists(xlsx_file): return
    if not os.path.exists(target_root): os.makedirs(target_root)
    tags = pd.read_excel(xlsx_file)
    patient_ids = tags['02_PatientID'].values
    for i, patient_id in enumerate(patient_ids):
        load = tags['07_Load'].values[i]
        if load == False: continue
        series_description = str(tags['05_SeriesDescription'].values[i])
        study_date = str(tags['03_StudyDate'].values[i])
        acqdatetime = str(tags['04_AcquisitionDateTime'].values[i])
        series_root_0 = str(tags['08_SeriesRoot'].values[i])
        series_files_strs = tags['09_SeriesFiles'].values[i]
        series_files_strs = series_files_strs.replace('\'', '')
        series_files_strs = series_files_strs.replace('[', '')
        series_files_strs = series_files_strs.replace(']', '')
        series_files_strs = series_files_strs.replace(' ', '')
        series_files = series_files_strs.split(',')
        series_root_1 = os.path.join(target_root, str(patient_id), study_date, acqdatetime + '_' + series_description)
        if not os.path.exists(series_root_1): os.makedirs(series_root_1)
        for file in series_files:
            filename = str(file)
            shutil.copyfile(os.path.join(series_root_0, filename), os.path.join(series_root_1, filename))
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
    dcm_root = '\\\\dataserver02\\PET-MR02\\11. 场地数据\北京宣武医院\\fMRI_PET'
    xlsx_file = 'E:\\xuanwu.xlsx'
    patient_roots = glob(os.path.join(dcm_root, '2019*', '*', 'Image', '*_*'))
    patient_roots += glob(os.path.join(dcm_root, '2019*', '*', '*_*'))
    for patient_root in patient_roots:
        try:
            print('working on %s'%(patient_root))
            dump_series2xlsx(patient_root, xlsx_file, mode='multi_per_dir')
        except:
            print('failed in converting %s'%(patient_root))
