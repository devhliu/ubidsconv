#----------------------------------------------------------------------------------------
#
#   Project - udcm2bids
#   Description:
#       A python processing package to convert UIH DICOM into bids format
#   File Name:    fmri_PET.py
#   Purpose:
#       to convert UIH specific dicom storage into bids format
#   Author: hui.liu02@united-imaging.com
#   Created 2019-06-13
#----------------------------------------------------------------------------------------


import os
import shutil
import pandas as pd


from glob import glob

project_root = '\\\\dataserver02\\PET-MR02\\11. 场地数据\\北京宣武医院\\fMRI_PET'
fmri_PET_ids = ['017','018','019','020','022','023','024','025','026','027','028','029',
                '031','033','035','036','044','047','060','064','066','068','069','071',
                '072','076','078','081','082','083','085','087','090','093','095','096',
                '097','100','101','103','105','108','109','110','114','115','119','123',
                '127','129','130']

info = {'ID':[], 'Name':[], 'Exist':[], 'Root':[]}
patient_roots = glob(os.path.join(project_root, '2019*', '*_*_*'))
for patient_root in patient_roots:
    patient_name_str = os.path.basename(patient_root)
    pns = patient_name_str.split('_')
    name = pns[0]
    id = pns[1]
    info['ID'].append(id)
    info['Name'].append(name)
    info['Exist'].append(id in fmri_PET_ids)
    info['Root'].append(patient_root)
df = pd.DataFrame(info)
df.sort_values(by=['ID'], ascending=True)
df.to_excel(os.path.join(project_root, 'info.xlsx'))