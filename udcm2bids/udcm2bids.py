#----------------------------------------------------------------------------------------
#
#   Project - udcm2bids
#   Description:
#       A python processing package to convert UIH DICOM into bids format
#   File Name:    udcm2bids.py
#   Purpose:
#       to convert UIH specific dicom storage into bids format
#   Author: hui.liu02@united-imaging.com
#   Created 2019-05-28
#----------------------------------------------------------------------------------------

import os
import json
import math
import pydicom
import subprocess
import numpy as np
import nibabel as nib

from glob import glob
from datetime import datetime
from datetime import timedelta

from .dcm2niix import dcm2niix

#----------------------------------------------------------------------------------------
#
# private utils functions
#
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#
def _diff_datetime(datetime_0, datatime_1):
    """
    :param datetime_0:
    :param datatime_1:
    :return:
    """
    acq_datetime_0 = datetime.strptime(datetime_0, '%Y%m%d%H%M%S')
    acq_datetime_1 = datetime.strptime(datatime_1, '%Y%m%d%H%M%S')
    delta_secs = acq_datetime_1 - acq_datetime_0
    return delta_secs.total_seconds()
#----------------------------------------------------------------------------------------
#
def _calc_uih_pet_suvbw_factor(ds):
    """
    :param ds:  pydicom.dataset
    :return:
    """
    if ds.Modality != 'PT': return 1.0
    if ds.Manufacturer != 'UIH': return 1.0

    # rescaleScople has been considering when converting to nifti1 format
    # doseCalibraFactor = float(ds.DoseCalibrationFactor)
    # rescaleSlope = float(ds.RescaleSlope)

    # read SUVbw tags from ds
    acqDateTime = ds.AcquisitionDateTime
    patientWeight = float(ds.PatientWeight)
    radionuclide = ds.RadiopharmaceuticalInformationSequence[0]
    radionuclideHalfLife = float(radionuclide.RadionuclideHalfLife)
    radionuclideTotalDose = float(radionuclide.RadionuclideTotalDose)
    radionuclideStartDateTime = radionuclide.RadiopharmaceuticalStartDateTime

    # calculation of bw factor
    bw_factor = 1000.0 * patientWeight / radionuclideTotalDose

    # calculation of decay factor
    acq_datetime_0 = datetime.strptime(str(acqDateTime)[:14], '%Y%m%d%H%M%S')
    acq_datetime_1 = datetime.strptime(str(radionuclideStartDateTime)[:14], '%Y%m%d%H%M%S')
    delta_secs = acq_datetime_0 - acq_datetime_1
    decay_lambda = math.log(2) / radionuclideHalfLife
    decay_factor = math.exp(decay_lambda * delta_secs.total_seconds())

    # correcting dose factor
    # dose_factor = rescaleSlope * doseCalibraFactor

    return decay_factor * bw_factor
#----------------------------------------------------------------------------------------
#
def _save_2_pet_suv_bqml(series_dicom_root, sub_root,
                         sub_name='sub-001',
                         func_name='pet',
                         task_name='rest'):
    """
    :param series_dicom_root:
    :param study_root:
    :param sub_name:
    :param func_name:
    :param task_name:
    :return:
    """
    # find suv tags and calc convert factor
    suv_factor = []
    acqdatetime = []
    dicom_files = glob(os.path.join(series_dicom_root, '*.dcm'))
    for i, file in enumerate(dicom_files):
        ds = pydicom.read_file(file, stop_before_pixels=False)
        dt = str(ds.AcquisitionDateTime)[:14]
        if dt not in acqdatetime:
            acqdatetime.append(dt)
            suv_factor.append(_calc_uih_pet_suvbw_factor(ds))
    # convert to bids
    func_root = os.path.join(sub_root, func_name)
    if not os.path.isdir(func_root): os.mkdir(func_root)
    # check whether exist or not
    bqml_nii_file = os.path.join(func_root,
                                 sub_name+'_task-'+task_name+'_PET-BQML.nii.gz')
    if not os.path.exists(bqml_nii_file):
        devnull = open(os.devnull, 'w')
        subprocess.call([dcm2niix, '-b', 'y', '-z', 'y',
                         '-f', sub_name + '_task-' + task_name + '_PET-BQML',
                         '-o', func_root, series_dicom_root],
                        stdout=devnull, stderr=subprocess.STDOUT)
    # convert bqml to suv_bw with suv_factor
    suvbw_nii_file = bqml_nii_file.replace('_PET-BQML', '_PET-SUVbw')
    suvbw_json_file = suvbw_nii_file.replace('.nii.gz', '.json')
    if os.path.exists(suvbw_nii_file): return
    nib_img_bqml = nib.load(bqml_nii_file)
    if len(suv_factor) > 1:
        nib_3d_imgs_bqml = nib.four_to_three(nib_img_bqml)
        np_3d_imgs_bqml = [nib_3d_img_bqml.get_data() for nib_3d_img_bqml in nib_3d_imgs_bqml]
        affines = [nib_3d_img_bqml.affine for nib_3d_img_bqml in nib_3d_imgs_bqml]
        np_3d_imgs_suvbw = [np_3d_img * c_factor
                            for np_3d_img, c_factor in zip(np_3d_imgs_bqml, suv_factor)]
        nib_3d_imgs_suvbw = [nib.Nifti1Image(new_np_3d_img, affine)
                             for new_np_3d_img, affine in zip(np_3d_imgs_suvbw, affines)]
        nib_img_suvbw = nib.concat_images(nib_3d_imgs_suvbw)
        nib_img_suvbw.to_filename(suvbw_nii_file)
    else:
        nib_3d_img_bqml = nib_img_bqml
        np_3d_img_bqml = nib_3d_img_bqml.get_data()
        affine = nib_3d_img_bqml.affine
        np_3d_img_suvbw = np_3d_img_bqml * suv_factor[0]
        nib_3d_img_suvbw = nib.Nifti1Image(np_3d_img_suvbw, affine)
        nib_3d_img_suvbw.to_filename(suvbw_nii_file)
    with open(suvbw_json_file, 'wt', encoding='utf-8') as f_json:
        json.dump({'suvbw_factor': suv_factor,
                   'acquisition_time': acqdatetime},
                  f_json,
                  indent=4)
    return
#----------------------------------------------------------------------------------------
#
def _save_2_generic(series_dicom_root, sub_root,
                    sub_name='sub-001',
                    func_name='func',
                    task_name='rest',
                    series_name='T1W'):
    """
    :param series_dicom_root:
    :param sub_root:
    :param sub_name:
    :param func_name:
    :param task_name:
    :param series_name:
    :return:
    """
    dicom_files = glob(os.path.join(series_dicom_root, '*.dcm'))
    for i, file in enumerate(dicom_files):
        ds = pydicom.read_file(file, stop_before_pixels=False)
        dt = str(ds.AcquisitionDateTime)[:14]
    # convert to bids
    func_root = os.path.join(sub_root, func_name)
    if not os.path.isdir(func_root): os.mkdir(func_root)
    # check whether exist
    nii_file = os.path.join(func_root, sub_name + '_task-' + task_name + '_' + series_name + '_.nii.gz')
    if os.path.exists(nii_file): return
    devnull = open(os.devnull, 'w')
    subprocess.call([dcm2niix, '-b', 'y', '-z', 'y',
                     '-f', sub_name + '_task-' + task_name + '_' + series_name,
                     '-o', func_root, series_dicom_root],
                    stdout=devnull, stderr=subprocess.STDOUT)
    return
#-----------------------------------------------------------------------------------
#
def convert_uih_dcm_2_bids(uih_dcm_root,
                           fmri_pet_study_root,
                           bids_func_info):
    """
    :param uih_dcm_root:
    :param fmri_pet_study_root:
    :param bids_func_info:      [{'series_description': 'epi_tra',
                                  'type': 'T1W' / 'BOLD' / 'DWI' / 'PET',
                                  'bids_func_name': 'anat',
                                  'bids_task_name': 'rest',
                                  'bids_session_name' : '01'}, ... ]

    :return:
    """
    # find the patient root defined as '*_*_*' - UIH specific exported dicom pattern
    patient_roots = glob(os.path.join(uih_dcm_root, '*', '*_*_*'))
    patient_roots += glob(os.path.join(uih_dcm_root, '*', 'Image', '*_*_*'))
    for patient_root in patient_roots:
        # create sub bids folders
        patient_name = os.path.basename(patient_root)
        sub_name = 'sub-' + str(patient_name.split('_')[1])
        sub_root = os.path.join(fmri_pet_study_root, sub_name)
        if not os.path.exists(sub_root): os.mkdir(sub_root)
        series_descriptions = os.listdir(patient_root)
        for bids_func in bids_func_info:
            i = 0
            for series_description in series_descriptions:
                if not bids_func.get('series_description') in series_description: continue
                print('working on %s - %s'%(sub_name, series_description))
                try:
                    dyn_sub_name = sub_name
                    dyn_sub_name + '-{:02d}'.format(i)
                    series_dicom_root = os.path.join(patient_root, series_description)
                    if bids_func.get('type') != 'PET':
                        _save_2_generic(series_dicom_root, sub_root, dyn_sub_name,
                                        func_name=bids_func.get('bids_func_name'),
                                        task_name=bids_func.get('bids_task_name'),
                                        series_name=bids_func.get('type'))
                    else:
                        _save_2_pet_suv_bqml(series_dicom_root, sub_root, dyn_sub_name,
                                             func_name=bids_func.get('bids_func_name'),
                                             task_name=bids_func.get('bids_task_name'))
                    i += 1
                except:
                    print('failed to convert %s - %s' %(sub_name, series_description))
    return
#----------------------------------------------------------------------------------------
#
# Test Purpose
#
#----------------------------------------------------------------------------------------
if __name__ == '__main__':
    dicom_root  = 'D:\\PD-control'
    bids_root   = 'D:\\PD-control_bids'
    if not os.path.exists(bids_root): os.mkdir(bids_root)
    bids_func_info = [{'series_description': 'epi_ra_',
                       'type': 'PET',
                       'bids_func_name': 'func',
                       'bids_task_name': 'rest'},
                      {'series_description': 'epi_dwi_tra_ADC_1009',
                       'type': 'PET',
                       'bids_func_name': 'func',
                       'bids_task_name': 'rest'},
                      {'series_description': 'epi_dwi_tra_ADC_134343',
                       'type': 'CT',
                       'bids_func_name': 'anat'}]
    convert_uih_dcm_2_bids(dicom_root, bids_root, bids_func_info)