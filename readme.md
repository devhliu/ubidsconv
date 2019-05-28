# U-DCM2BIDS

This repository provides easy to convert UIH dicom into bids format for further processing.

## Installation Instructions 

1) Clone this repository:
    ```bash
    git clone https://github.com/devhliu/udcm2bids.git
    ```
2) Go into the repository (the folder with the setup.py file) and install:
    ```
    cd udcm2bids
    pip install -e .
    ```

## How to use it 

Using HD_BET is straightforward. You can use it in any terminal on your linux system. The hd-bet command was installed 
automatically. We provide CPU as well as GPU support. Running on GPU is a lot faster though 
and should always be preferred. Here is a minimalistic example of how you can use HD-BET (you need to be in the HD_BET 
directory)

```bash
hd-bet -i INPUT_FILENAME
```

INPUT_FILENAME must be a nifti (.nii.gz) file containing 3D MRI image data. 4D image sequences are not supported 
(however can be splitted upfront into the individual temporal volumes using fslsplit<sup>1</sup>). 
INPUT_FILENAME can be either a pre- or postcontrast T1-w, T2-w or FLAIR MRI sequence. Other modalities might work as well.
Input images must match the orientation of standard MNI152 template! Use fslreorient2std <sup>2</sup> upfront to ensure 
that this is the case.

By default, HD-BET will run in GPU mode, use the parameters of all five models (which originate from a five-fold 
cross-validation), use test time data augmentation by mirroring along all axes and not do any postprocessing.

For batch processing it is faster to process an entire folder at once as this will mitigate the overhead of loading 
and initializing the model for each case:

```bash
hd-bet -i INPUT_FOLDER -o OUTPUT_FOLDER
```

The above command will look for all nifti files (*.nii.gz) in the INPUT_FOLDER and save the brain masks under the same name
in OUTPUT_FOLDER.

### GPU is nice, but I don't have one of those... What now? 

HD-BET has CPU support. Running on CPU takes a lot longer though and you will need quite a bit of RAM. To run on CPU, 
we recommend you use the following command:

```bash
hd-bet -i INPUT_FOLDER -o OUTPUT_FOLDER -device cpu -mode fast -tta 0
```
This works of course also with just an input file:

```bash
hd-bet -i INPUT_FILENAME -device cpu -mode fast -tta 0
```

The options *-mode fast* and *-tta 0* will disable test time data augmentation (speedup of 8x) and use only one model instead of an ensemble of five models 
for the prediction.

### More options:
For more information, please refer to the help functionality:

```bash
hd-bet --help
```

## FAQ

1) **How much GPU memory do I need to run HD-BET?**  
We ran all our experiments on NVIDIA Titan X GPUs with 12 GB memory. For inference you will need less, but since 
inference in implemented by exploiting the fully convolutional nature of CNNs the amount of memory required depends on 
your image. Typical image should run with less than 4 GB of GPU memory consumption. If you run into out of memory
problems please check the following: 1) Make sure the voxel spacing of your data is correct and 2) Ensure your MRI 
image only contains the head region
2) **Will you provide the training code as well?**  
No. The training code is tightly wound around the data which we cannot make public.
3) **What run time can I expect on CPU/GPU?**  
This depends on your MRI image size. Typical run times (preprocessing, postprocessing and resampling included) are just
 a couple of seconds for GPU and about 2 Minutes on CPU (using ```-tta 0 -mode fast```)
