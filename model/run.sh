#!/usr/bin/env bash
python main.py --input ../data/fasttext_wiki_size_300_min_count_5_iter_50_negative_20.hdf5 \
		 --num_epochs 4000 \
		 --denoising \
		 --noise 0.2 \
		 --sparsity 0.85 \
		 --output ../data/fasttext_wiki_size_300_min_count_5_iter_50_negative_20_spine.hdf5 \
		 --hdim 1000 \
         --gpu_idx 0 \
		 --batch_size 64
