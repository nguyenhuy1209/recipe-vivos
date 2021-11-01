#!/usr/bin/env bash

# Copyright 2019 National Institute of Informatics (Hieu-Thi Luong)
#  Apache 2.0 (http://www.apache.org/licenses/LICENSE-2.0)

# . ./path.sh || exit 1;
# . ./cmd.sh || exit 1;

# general configuration
stage=1           # start from 1 to download VIVOS corpus
stop_stage=10

# data
datadir=./data
vivos_root=${datadir}/vivos
working_data_dir=${vivos_root}
data_url=https://ailab.hcmus.edu.vn/assets/vivos.tar.gz

# Pitch shifting related
use_ps=true
pitch_shifting_step=1
vivos_ps=${datadir}/vivos_ps_${pitch_shifting_step}

# Speed perturbation related
use_sp=true
speed_perturb_factors=0.9
vivos_sp=${datadir}/vivos_sp_${speed_perturb_factors}

# Noise augumentation related
use_noise_aug=true
noise_path=noise/xe3.wav
vivos_aug=${datadir}/vivos_aug

# exp tag
tag=""

. utils/parse_options.sh || exit 1;

set -e
set -u
set -o pipefail

if [ ${stage} -le 1 ] && [ ${stop_stage} -ge 1 ]; then
    echo "stage 1: Data download"

    mkdir -p ${datadir}
    local/download_and_untar.sh ${datadir} ${data_url}
fi


if [ ${stage} -le 2 ] && [ ${stop_stage} -ge 2 ]; then
    echo "Stage 2: Pitch shifting"
    if [ ${use_ps} == true ]; then 
        if [ -d $vivos_ps ]; then
            echo "$0: pitch shifting directory already exists in $vivos_ps"
        else
            for x in test train; do
                python3 local/pitch_shift.py             \
                    --audio_folder_path ${working_data_dir}/$x  \
                    --output_folder_path ${vivos_ps}/$x         \
                    --n_steps ${pitch_shifting_step}                 
            done
        fi
        working_data_dir=${vivos_ps}
    else
        echo "Skipping pitch shifting..."
    fi
fi

if [ ${stage} -le 3 ] && [ ${stop_stage} -ge 3 ]; then
    echo "Stage 3: Speed perturbation"
    if [ ${use_sp} == true ]; then 
        if [ -d $vivos_sp ]; then
            echo "$0: speed perturbation directory already exists in $vivos_sp"
        else
            for x in test train; do
                python3 local/speed_perturbation.py             \
                    --audio_folder_path ${working_data_dir}/$x  \
                    --output_folder_path ${vivos_sp}/$x         \
                    --rate ${speed_perturb_factors}             
            done  
        fi
        working_data_dir=${vivos_sp}
    else
        echo "Skipping speed perturbation..."
    fi
fi

if [ ${stage} -le 4 ] && [ ${stop_stage} -ge 4 ]; then
    echo "stage 4: Noise augumentation"

    if [ ${use_noise_aug} == true ]; then 
        if [ -d $vivos_aug ]; then
            echo "$0: noise augumentation directory already exists in $vivos_aug"
        else
            for x in test train; do
                python3 local/add_noise.py                  \
                    --audio_folder_path ${vivos_root}/$x    \
                    --noise_path ${noise_path}              \
                    --output_folder_path ${vivos_aug}/$x
            done
        fi
        working_data_dir=${vivos_aug}
    else
        echo "Skipping noise augumentation..."
    fi
fi

if [ ${stage} -le 5 ] && [ ${stop_stage} -ge 5 ]; then
    echo "stage 5: Data preparation"

    # mkdir -p data/{train,test} exp
    mkdir -p data/{train,test}

    if [ ! -f ${vivos_root}/README ]; then
        echo "Cannot find vivos root! Exiting..."
        exit 1;
    fi
    
    for x in test train; do
        awk -v dir=${working_data_dir}/$x '{ split($1,args,"_"); spk=args[1]; print $1" "dir"/waves/"spk"/"$1".wav" }' ${vivos_root}/$x/prompts.txt | sort > data/$x/wav.scp
        awk '{ split($1,args,"_"); spk=args[1]; print $1" "spk }' ${vivos_root}/$x/prompts.txt | sort > data/$x/utt2spk
        sort ${vivos_root}/$x/prompts.txt > data/$x/text
        utils/utt2spk_to_spk2utt.pl data/$x/utt2spk > data/$x/spk2utt
    done
fi