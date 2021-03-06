"""
Released under BSD 3-Clause License, 
Modifications are Copyright (c) 2019 Cerebras, Inc.
All rights reserved.
"""
import argparse
import os
import random
import warnings

import torch
from torch.backends import cudnn
from torchvision import transforms
from torchvision import datasets

from model import model as models
from utils import main_worker

NUM_CLASSES = 10

model_names = sorted(name for name in models.__dict__
    if name.islower() and not name.startswith("__")
    and callable(models.__dict__[name]))

parser = argparse.ArgumentParser(description='PyTorch ImageNet Training')
parser.add_argument('data', metavar='DIR',
                    help='path to dataset')
parser.add_argument('--model_dir', type=str, default='./model_dir',
                    help='dir to which model is saved (default: ./model_dir)')
parser.add_argument('-d', '--depth', default=20, type=int, metavar='D',
                    help='depth of ResNet (default: 20)')
parser.add_argument('-j', '--workers', default=4, type=int, metavar='N',
                    help='number of data loading workers (default: 4)')
parser.add_argument('--epochs', default=250, type=int, metavar='N',
                    help='number of total epochs to run (default: 250)')
parser.add_argument('--start-epoch', default=0, type=int, metavar='N',
                    help='manual epoch number (useful on restarts, default: 0)')
parser.add_argument('-b', '--batch-size', default=128, type=int,
                    metavar='N',
                    help='mini-batch size (default: 128)')
parser.add_argument('--lr', '--learning-rate', default=0.1, type=float,
                    metavar='LR', help='initial learning rate (default: 0.1)',
                    dest='lr')
parser.add_argument('--lr_milestones', nargs='+', type=int,
                        default=[100, 150, 200],
                        help='epochs at which we take a learning-rate step '
                             '(default: [100, 150, 200])')
parser.add_argument('--lr_multiplier', default=0.1, type=float, metavar='M',
                    help='lr multiplier at lr_milestones (default: 0.1)')
parser.add_argument('--momentum', default=0.9, type=float, metavar='M',
                    help='optimizer momentum (default: 0.9)')
parser.add_argument('--wd', '--weight-decay', default=2e-4, type=float,
                    metavar='W', help='weight decay (default: 2e-4)',
                    dest='weight_decay')
parser.add_argument('-p', '--print-freq', default=10, type=int,
                    metavar='N', help='print frequency (default: 10)')
parser.add_argument('--resume', default='', type=str, metavar='PATH',
                    help='path to latest checkpoint (default: none)')
parser.add_argument('-e', '--evaluate', dest='evaluate', action='store_true',
                    help='evaluate model on validation set')
parser.add_argument('--pretrained', dest='pretrained', action='store_true',
                    help='use pre-trained model')
parser.add_argument('--seed', default=None, type=int,
                    help='seed for initializing training')
parser.add_argument('--norm_mode', default='batch', type=str,
                    metavar='NORM',
                    help='select normalization type. options: "batch" | '
                         '"group" | "layer" | "instance" | "online" | '
                         '"none". (default: batch)')
parser.add_argument('--afwd', '--decay_factor_forward', default=1023 / 1024,
                    type=float, metavar='AFWD', dest='afwd',
                    help='forward decay factor which sets momentum process '
                         'hyperparameter when using online normalization '
                         '(default: 1023 / 1024)')
parser.add_argument('--abkw', '--decay_factor_backward', default=127 / 128,
                    type=float, metavar='ABKW', dest='abkw',
                    help='backward decay factor which sets control process '
                         'hyperparameter when using online normalization '
                         '(default: 127 / 128)')
parser.add_argument('--rm_layer_scaling', action='store_true',
                    help='remove layer scaling in online normalization '
                         '(default: False)')
parser.add_argument('--gn_num_groups', default=8, type=int,
                    help='number of groups in group norm if using group norm '
                         'as normalization method (default: 8)')
args = parser.parse_args()


def main(args):
    if args.seed is not None:
        random.seed(args.seed)
        torch.manual_seed(args.seed)
        cudnn.deterministic = True
        warnings.warn('You have chosen to seed training. '
                      'This will turn on the CUDNN deterministic setting, '
                      'which can slow down your training considerably! '
                      'You may see unexpected behavior when restarting '
                      'from checkpoints.')

    # Data loading code
    traindir = os.path.join(args.data, 'train')
    valdir = os.path.join(args.data, 'val')
    print('=> create train dataset')
    normalize = transforms.Normalize(mean=[0.4914, 0.4822, 0.4465],
                                     std=[0.2470, 0.2435, 0.2616])

    train_transform = transforms.Compose([transforms.Pad(4),
                                          transforms.RandomCrop(size=32),
                                          transforms.RandomHorizontalFlip(),
                                          transforms.ToTensor(), normalize])
    train_dataset = datasets.CIFAR10(traindir, train=True,
                                     transform=train_transform,
                                     target_transform=None,
                                     download=True)

    print('=> create train dataloader')
    train_loader = torch.utils.data.DataLoader(train_dataset,
                                               batch_size=args.batch_size,
                                               shuffle=True,
                                               num_workers=args.workers,
                                               pin_memory=True,
                                               drop_last=True)

    print('=> create val dataset')
    val_transform = transforms.Compose([transforms.ToTensor(), normalize])
    val_dataset = datasets.CIFAR10(valdir, train=False,
                                   transform=val_transform,
                                   target_transform=None,
                                   download=True)

    print('=> create val dataloader')
    print('=> creating validation dataloader...')
    val_loader = torch.utils.data.DataLoader(val_dataset,
                                             batch_size=args.batch_size,
                                             shuffle=False,
                                             num_workers=args.workers,
                                             pin_memory=True)

    main_worker(train_loader, val_loader, NUM_CLASSES, args, cifar=True)


if __name__ == '__main__':
    os.makedirs(args.model_dir, exist_ok=True)
    main(args)
