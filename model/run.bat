python main.py --input ../data/wiki-news-300d-1M-subword.hdf5 ^
		 --num_epochs 500 ^
		 --denoising ^
		 --noise 0.2 ^
		 --sparsity 0.85 ^
		 --hdim 1000 ^
         --gpu_idx 0 ^
		 --batch_size 64 ^
		 --optim adam