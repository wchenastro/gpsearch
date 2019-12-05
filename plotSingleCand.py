#!/usr/bin/env python

import sys, csv
from sigpyproc import FilReader
from matplotlib import pyplot as plt
import numpy as np


filFileName = sys.argv[1]
candIndex = sys.argv[2]
plotDirectory = sys.argv[3]
DM = sys.argv[4]
window = int(sys.argv[5])
fullSpan = int(sys.argv[6])
rfiChanStart = 7

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
#plt.subplot(121)
plt.imshow(dblock, cmap="YlOrBr_r", interpolation="nearest", aspect="auto")
#plt.subplot(122)
#plt.plot(dblock.sum(axis=0))
if plotDirectory == "0":
    plt.show()
else:
    plt.savefig("{}/{}.png".format(plotDirectory, name))
