#!/usr/bin/env python

import os, sys, csv
import numpy as np
import matplotlib; matplotlib.use('Agg')
from matplotlib import pyplot as plt
import matplotlib.gridspec as GridSpec
from sigpyproc import FilReader


filFileName = sys.argv[1]
candFile = sys.argv[2]
plotDirectory = sys.argv[3]
DM = sys.argv[4]
maxWindow = int(sys.argv[5])
fullSpan = int(sys.argv[6])
rfiChanStart = 7

cands = np.loadtxt(candFile, ndmin=2)
basename = os.path.basename(filFileName)
filReader = FilReader(filFileName)

for cand in cands:
    candIndex = cand[1]
    timestamp = cand[2]
    pulseWidth = int(cand[8]) - int(cand[7])
    windowWidth = pulseWidth*256
    windowWidth = maxWindow if maxWindow <= windowWidth else windowWidth
    SNR = cand[0]
    center = int(candIndex)
    span = (center - fullSpan/2, center + fullSpan/2)
    block = filReader.readBlock(span[0], span[1]-span[0])
    dblock = block
    dblock = dblock.dedisperse(float(DM))
    aCenter = (fullSpan-2)/2
    dblock = dblock[:, aCenter-windowWidth/2:aCenter+windowWidth/2]
    # neutralize these channels
    if len(sys.argv) >= rfiChanStart:
        avgValue = np.sum(dblock)*1.0/(dblock.shape[0]*dblock.shape[1])
        chans = sys.argv[rfiChanStart:]
        for i in range(0, len(chans), 2):
            dblock[int(chans[i]):int(chans[i+1]), :] = avgValue

    height = dblock.shape[0]
    width = dblock.shape[1]
    score = 0
    rfi = False
    bscrunch = dblock.sum(axis=1)
    # fscrunch = dblock.sum(axis=0)
    # average = 1.* bscrunch.sum() / (height * width)
    bscrunch80max = bscrunch.max()*0.98
    channelStrong = np.where(bscrunch > bscrunch80max)[0]
    if len(channelStrong) < (height * 0.05):
        score += 1.2
    for i in channelStrong:
        chanBlock = dblock[i,:]
        if len(chanBlock[chanBlock > chanBlock.max()*0.98]) > 7 * pulseWidth:
            score += 1.3
            break

    if score > 1.5:
        rfi = True

    if rfi != True and pulseWidth != 0:
        convolveWdith = pulseWidth if pulseWidth < maxWindow else maxWindow
        for chan in range(len(dblock)):
            try:
                dblock[chan] = np.convolve(
                        dblock[chan], np.ones(convolveWdith), 'same')
            except:
                pass
    fig = plt.figure(constrained_layout=True)
    gridspec = GridSpec.GridSpec(ncols=5, nrows=5, figure=fig,  wspace=0.0, hspace=0.0)
    ax_top = fig.add_subplot(gridspec[0, 0:4])
    ax_center = fig.add_subplot(gridspec[1:, 0:4])
    ax_right = fig.add_subplot(gridspec[1:, 4:])
    ax_top.plot(range(dblock.shape[1]), dblock.sum(axis=0), "k", lw=0.7)
    ax_top.margins(x=0)
    ax_top.set_xticks([])
    ax_top.set_yticks([])
    ax_center.imshow(dblock, cmap="YlOrBr_r", interpolation="nearest", aspect="auto")
    ax_right.plot(dblock.sum(axis=1), range(dblock.shape[0])[::-1], "k", lw=0.7)
    ax_right.margins(y=0)
    ax_right.set_xticks([])
    ax_right.set_yticks([])
    plt.tight_layout()
    plt.suptitle("{0}\n index: {1}, time: {2} sec, S/N: {3} RFI score: {4}".format(
                basename, candIndex, timestamp, SNR, score))
    plt.subplots_adjust(top=0.90, left=0.1, bottom=0.1)
    ax_center.set_xlabel('bin')
    ax_center.set_ylabel('channel')
    if rfi != True:
        plt.savefig("{}/{}.png".format(plotDirectory, candIndex))
    else:
        plt.savefig("{}/rfi/{}.png".format(plotDirectory, candIndex))
