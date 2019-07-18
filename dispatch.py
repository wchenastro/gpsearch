#!/usr/bin/env python

import sys, os, signal
import subprocess
import logging
import argparse

import notify

if len(sys.argv) < 4:
    print("insufficient arguments")
    exit(-1)
if int(sys.argv[1]) < 1:
    print("interval should not be less then 1")
    exit(-1)

def signal_handler(sig, frame):
    logger.debug("job was cancelled by user at %s" % hostname)
    sys.exit(0)

def signal_kill_handler(sig, frame):
    message = "job was kill at %s" % hostname
    logger.debug(message)
    notify.send("job killed", message, "dspsr@pacifix")
    sys.exit(0)


def parseOptions(parser):
    parser.add_argument('--data', nargs=1, metavar="directory", help='dada file directory')
    parser.add_argument('--output', nargs=1, metavar="directory", help='output file directory')
    parser.add_argument('--sub', nargs=1, metavar="directory", help='sub directory for output')
    parser.add_argument('--total', nargs=1, metavar="num", help="total parts")
    parser.add_argument('--part', nargs=1, metavar="num", help="part index")
    parser.add_argument('--thread', nargs=1, metavar="num", help="thread number, default: none")
    parser.add_argument('--group', nargs=1, metavar="num", help="number of file of each iteration")
    parser.add_argument('--channel', nargs=1, metavar="num", help="number of channel")

    args = parser.parse_args()

basePath ='/home/psr/workspace'
dataPath = basePath + '/data/20190511/J2229+6114'
# dataPath = basePath + '/data/20190511/J2215+5135'
# resultPath = basePath + '/search'
resultPath = basePath + '/fold'
logPath = basePath + '/logs'

#dsprCommand = "dspsr -E %s/pulsar.par -P %s/t2pred.dat \
#	 -F 256:D -t 16 -s -minram=4 -J %s/gpsearch.sh " % (basePath, basePath, basePath)

# dsprCommand = "dspsr -F 256:D -t 16 -s -K -minram=4 -J %s/gpsearch.sh " % basePath
# dsprCommand = "dspsr -F 32:D -b 8192 -D 71.0179 -t 16 -s -K -minram=8 -J %s/gpsearch.sh " % basePath
dsprCommand = "dspsr -F 256:D -E %s/J2229+6114.par -t 16 -minram=4 -L 10 -A " % basePath
# dsprCommand = "dspsr -F 256:D -E %s/J2215+5135.par -t 16 -minram=4 -L 10 -A " % basePath
# dsprCommand = "dspsr -F 256:D  -c 0.051666999654 -D 204.468 -t 16 -minram=4 -L 10 -A "
# dsprCommand = "dspsr -F 32:D -b 8192 -E %s/J2229+6114.par -t 16 -s -K -minram=8 -J %s/gpsearch.sh " %  (basePath, basePath)

stackInterval = int(sys.argv[1])
thisPart = sys.argv[2]
totalParts = sys.argv[3]
outputPath = resultPath + '/' + thisPart


logsFileName = logPath + '/log'
if os.path.isfile(logsFileName):
    if os.path.getsize(logsFileName) > 2000000:
        os.rename(logsFileName, logsFileName + '.bak')
loggerFormat = '%(asctime)-15s  %(filename)s  %(message)s'
logging.basicConfig(filename=logsFileName , format = loggerFormat, level=logging.DEBUG)
logger = logging.getLogger(__name__)

hostname = os.uname()[1]


logger.debug("job started at %s with parameters %s" % (hostname, " ".join(sys.argv)))
if(not os.path.isdir(outputPath)):
    os.mkdir(outputPath)
os.chdir(outputPath)
allFiles = [os.path.join(dataPath, fileName) for fileName in os.listdir(dataPath)]
allFiles.sort()
fileNum = len(allFiles)
groupSize = fileNum/int(totalParts) + (1 if (fileNum % int(totalParts)) > 0 else 0)
groupStart = int(thisPart)*groupSize
groupEnd = groupStart + groupSize
if groupEnd > fileNum:
    groupEnd = fileNum
thisGroup = allFiles[groupStart:groupEnd]

segments = []
currentTime = ''
for dataFile in thisGroup:
    dataTime = dataFile.split('/')[-1].split('_')[0]
    if dataTime != currentTime:
        segments.append([])
        currentTime = dataTime
    segments[-1].append(dataFile)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_kill_handler)
retryCount = 0
processCount = 0
for segment in segments:
    #thisFileList = ' '.join(segment)
    #os.system(dsprCommand + thisFileList)
    stackNum = len(segment)
    stackIdx = 0
    while stackIdx < stackNum:
        stackEnd = stackIdx + stackInterval
        if stackEnd < stackNum:
            stackList = segment[stackIdx:stackEnd]
        else:
            stackList = segment[stackIdx:]
        stackIdx = stackEnd

        thisFileList = ' '.join(stackList)
        try:
            output = subprocess.check_output(dsprCommand + thisFileList, shell=True)
            #output = subprocess.check_output('exit 1', shell=True)
            #output = subprocess.check_output('ls', shell=True)
            retryCount = 0
            processCount += len(stackList)
            #logger.debug("finished on these files: %s at %s" % (thisFileList, hostname))
        except subprocess.CalledProcessError as e:
        #process = subprocess.Popen('exit 1', shell=True, stderr=subprocess.PIPE)
        #if process.returncode != 0:
            message = "job exits unexpected at %s" % hostname
            logger.debug(message)
	    notify.send("job exits", message, "dspsr@pacifix")
            # logger.debug(output)
            if retryCount < 10:
                retryCount = retryCount + 1
                logger.debug(e.strerror)
                logger.debug("retry the file")
                stackIdx = stackIdx - stackInterval
            else:
                retryCount = 0
                logger.debug("max retry reached, skip files: %s at %s" % (thisFileList, hostname))
        #logger.debug("job finished a segment at %s" % hostname)

message = "job stopped at %s after successfully processing %d files with parameters %s" % (
                hostname, processCount, " ".join(sys.argv))
logger.debug(message)
notify.send("job stopped", message, "dspsr@pacifix")