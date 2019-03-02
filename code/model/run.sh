#!/usr/bin/env bash
python main.py --input ../data/wiki-news-300d-1M-subword.hdf5 \
		 --num_epochs 4000 \
		 --denoising \
		 --noise 0.2 \
		 --sparsity 0.85 \
		 --output ../data/wiki-news-300d-1M-subword-spine.hdf5 \
		 --hdim 1000 \
         --gpu_idx 1
