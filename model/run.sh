#!/usr/bin/env bash
INPUT="$1"
EPOCHS="$2"
GPU="$3"
python main.py --input "${INPUT}" \
		 --num_epochs ${EPOCHS} \
		 --denoising \
		 --noise 0.2 \
		 --sparsity 0.85 \
		 --hdim 1000 \
         --gpu_idx ${GPU} \
		 --batch_size 64 \
         --optim adam
