#!/bin/bash
#SBATCH --gres=gpu:1
#SBATCH --mail-type=ALL # required to send email notifcations
#SBATCH --mail-user=db620 # required to send email notifcations - please replace <your_username> with your college login name or email address
export PATH=/vol/bitbucket/${USER}/venv/bin/:$PATH
# the above path could also point to a miniconda install
# if using miniconda, uncomment the below line
# source ~/.bashrc
source activate
if [ -f /vol/cuda/12.2.0/setup.sh ]; then
    . /vol/cuda/12.2.0/setup.sh
fi
/usr/bin/nvidia-smi
uptime
# cd /vol/bitbucket/${USER}
# python3 test.py
cd /vol/bitbucket/${USER}/yolov5
python train.py --img 640 --batch 16 --epochs 100 --data data/dataset.yaml --weights yolov5s.pt --cache