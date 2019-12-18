#!/usr/bin/env python

import os, sys, csv
import numpy as np
import matplotlib; matplotlib.use('Agg')
from matplotlib import pyplot as plt
from sigpyproc import FilReader


filFileName = sys.argv[1]
candFile = sys.argv[2]
plotDirectory = sys.argv[3]
DM = sys.argv[4]
window = int(sys.argv[5])
fullSpan = int(sys.argv[6])
rfiChanStart = 7

cands = np.loadtxt(candFile, ndmin=2)
basename = os.path.basename(filFileName)
filReader = FilReader(filFileName)

for cand in cands:
    candIndex = cand[1]
    timestamp = cand[2]
    width = int(cand[8]) - int(cand[7])
    SNR = cand[0]
    center = int(candIndex)
    span = (center - fullSpan/2, center + fullSpan/2)
    block = filReader.readBlock(span[0], span[1]-span[0])
    dblock = block
    dblock = dblock.dedisperse(float(DM))
    aCenter = (fullSpan-2)/2
    dblock = dblock[:, aCenter-window/2:aCenter+window/2]
    # neutralize these channels
    if len(sys.argv) >= rfiChanStart:
        avgValue = np.sum(dblock)*1.0/(dblock.shape[0]*dblock.shape[1])
        chans = sys.argv[rfiChanStart:]
        for i in range(0, len(chans), 2):
            dblock[int(chans[i]):int(chans[i+1]), :] = avgValue
    if width != 0:
        for chan in range(len(dblock)):
            dblock[chan] = np.convolve(dblock[chan], np.ones(width), 'same')
    plt.imshow(dblock, cmap="YlOrBr_r", interpolation="nearest", aspect="auto")
    plt.title("{0}\n index: {1}, time: {2} sec, S/N: {3}".format(
                basename, candIndex, timestamp, SNR))
    plt.xlabel('bin')
    plt.ylabel('channel')
    plt.savefig("{}/{}.png".format(plotDirectory, candIndex))
