import torch
from torch import nn
from torch.autograd import Variable
from torch.optim.lr_scheduler import StepLR
import argparse
import utils
from utils import DataHandler
from model import SPINEModel
from random import shuffle
import numpy as np
import logging
import math
import h5py
import json
from pathlib import Path
logging.basicConfig(level=logging.INFO)


#########################################################

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--hdim', dest='hdim', type=int, default=1000,
                    help='resultant embedding size')

parser.add_argument('--denoising', dest='denoising',
                                        default=False,
                                        action='store_true',
                    help='noise amount for denoising auto-encoder')

parser.add_argument('--noise', dest='noise_level', type=float,
                    default=0.2,
                    help='noise amount for denoising auto-encoder')

parser.add_argument('--num_epochs', dest='num_epochs', type=int,
                    default=100,
                    help='number of epochs')

parser.add_argument('--batch_size', dest='batch_size', type=int,
                    default=64,
                    help='batch size')

parser.add_argument('--sparsity', dest='sparsity', type=float,
                    default=0.85,
                    help='sparsity')

parser.add_argument('--input', dest='input',
                    default="data/glove.6B.300d.txt",
                    help='input src')

# parser.add_argument('--output', dest='output',
# 					default = "data/glove.6B.300d.txt.spine" ,
#                     help='output')

parser.add_argument('--optim', dest='optim', default='sgd',
                    help='The optimizer to use (sgd | adam)')

parser.add_argument('--gpu_idx', dest='gpu_idx', default=0,
                    type=int, help='The index of GPU to use')

#########################################################


class Solver:

    def __init__(self, params):

        # Build data handler
        self.data_handler = DataHandler()
        self.data_handler.loadData(params['input'])
        params['inp_dim'] = self.data_handler.getDataShape()[1]
        logging.info("="*41)

        # Build model
        self.model = SPINEModel(params)
        self.dtype = torch.FloatTensor
        use_cuda = torch.cuda.is_available()
        if use_cuda:
            self.model.cuda()
            self.dtype = torch.cuda.FloatTensor
        # Select optimizer
        optim_selected = params['optim']
        LR = 0.1
        if optim_selected == 'sgd':
            self.optimizer = torch.optim.SGD(self.model.parameters(), lr=LR)
        elif optim_selected == 'adam':
            self.optimizer = torch.optim.Adam(self.model.parameters(), lr=LR)
        logging.info("="*41)

    def train(self, params):
        num_epochs, batch_size = params['num_epochs'], params['batch_size'],
        optimizer = self.optimizer
        dtype = self.dtype
        STEP_DENOM = 5
        scheduler = StepLR(optimizer, step_size=math.ceil(num_epochs / STEP_DENOM), gamma=0.3)
        for iteration in range(num_epochs):
            # lr adjusting
            scheduler.step()
            # start epoch
            self.data_handler.shuffleTrain()
            num_batches = self.data_handler.getNumberOfBatches(batch_size)
            epoch_losses = np.zeros(4)  # rl, asl, psl, total
            for batch_idx in range(num_batches):
                optimizer.zero_grad()
                batch_x, batch_y = self.data_handler.getBatch(
                    batch_idx, batch_size, params['noise_level'], params['denoising'])
                batch_x = Variable(torch.from_numpy(
                    batch_x), requires_grad=False).type(dtype)
                batch_y = Variable(torch.from_numpy(
                    batch_y), requires_grad=False).type(dtype)
                out, h, loss, loss_terms = self.model(batch_x, batch_y)
                reconstruction_loss, psl_loss, asl_loss = loss_terms
                loss.backward()
                epoch_losses[0] += reconstruction_loss.data.item()
                epoch_losses[1] += asl_loss.data.item()
                epoch_losses[2] += psl_loss.data.item()
                epoch_losses[3] += loss.data.item()
                optimizer.step()
            
            print("After epoch %r, Reconstruction Loss = %.4f, ASL = %.4f, "
                  "PSL = %.4f, and total = %.4f"
                  % (iteration+1, epoch_losses[0], epoch_losses[1], epoch_losses[2], epoch_losses[3]))
            # logging.info("After epoch %r, Sparsity = %.1f"
            #			%(iteration+1, utils.compute_sparsity(h.cpu().data.numpy())))
            # break
            # break

    def getSpineEmbeddings(self, batch_size, params):
        ret = []
        self.data_handler.resetDataOrder()
        num_batches = self.data_handler.getNumberOfBatches(batch_size)
        for batch_idx in range(num_batches):
            batch_x, batch_y = self.data_handler.getBatch(
                batch_idx, batch_size, params['noise_level'], params['denoising'])
            batch_x = Variable(torch.from_numpy(batch_x),
                               requires_grad=False).type(self.dtype)
            batch_y = Variable(torch.from_numpy(batch_y),
                               requires_grad=False).type(self.dtype)
            _, h, _, _ = self.model(batch_x, batch_y)
            ret.extend(h.cpu().data.numpy())
        return np.array(ret)

    def getWordsList(self):
        return self.data_handler.getWordsList()


#########################################################

def get_param_string(params):
    vals = []
    for k in ['hdim', 'batch_size', 'num_epochs', 'sparsity', 'optim']:
        vals.append(k)
        vals.append(str(params[k]))
    return '_'.join(vals)


def main():

    params = vars(parser.parse_args())
    input_path = Path(params['input'])
    output_path = input_path.parent / \
        (input_path.name.split('.')[0] + '_' +
            get_param_string(params) + '.hdf5.spine')
    params['output'] = str(output_path)

    logging.info("PARAMS = " + str(params))
    logging.info("="*41)
    with torch.cuda.device(params['gpu_idx']):
        solver = Solver(params)
        solver.train(params)
        # dumping the final vectors
        logging.info("Dumping the final SPine embeddings")
        final_batch_size = 512
        with h5py.File(output_path, 'w') as f:
            words = solver.getWordsList()
            vectors = solver.getSpineEmbeddings(final_batch_size, params)
            f.create_dataset('words', data=words, dtype=h5py.special_dtype(
                vlen=str), compression='gzip')
            f.create_dataset('vectors', data=vectors, compression='gzip')
        # Save params
        with open(str(output_path) + '.json', 'w', encoding='utf-8') as fout:
            json.dump(params, fout, indent=4)

if __name__ == '__main__':
    main()
