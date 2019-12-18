#!/usr/bin/env python

import sys, csv
from sigpyproc import FilReader
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np


filFileName = sys.argv[1]
candIndex = sys.argv[2]
plotDirectory = sys.argv[3]
DM = sys.argv[4]
window = int(sys.argv[5])
fullSpan = int(sys.argv[6])
width = int(sys.argv[7])
rfiChanStart = 8

filReader = FilReader(filFileName)
center = int(candIndex)
span = (center - fullSpan/2, center + fullSpan/2)
block = filReader.readBlock(span[0], span[1]-span[0])
dblock = block
dblock = dblock.dedisperse(float(DM))
aCenter = (fullSpan-2)/2
dblock = dblock[:, aCenter-window/2:aCenter+window/2]
#dblock = dblock.downsample(60)
# neutralize these channels
if len(sys.argv) >= rfiChanStart:
    avgValue = np.sum(dblock)*1.0/(dblock.shape[0]*dblock.shape[1])
    chans = sys.argv[rfiChanStart:]
    for i in range(0, len(chans), 2):
        dblock[int(chans[i]):int(chans[i+1]), :] = avgValue
if width != 0:
    for chan in range(len(dblock)):
        dblock[chan] = np.convolve(dblock[chan], np.ones(width), 'same')
fig = plt.figure(constrained_layout=True)
gridspec = gridspec.GridSpec(ncols=5, nrows=5, figure=fig,  wspace=0.0, hspace=0.0)
ax_top = fig.add_subplot(gridspec [0, 0:4])
ax_center = fig.add_subplot(gridspec [1:, 0:4])
ax_right = fig.add_subplot(gridspec [1:, 4:])
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
if plotDirectory == "0":
    plt.show()
else:
    plt.savefig("{}/{}.png".format(plotDirectory, name))
