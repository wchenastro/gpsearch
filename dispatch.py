#!/usr/bin/env python

import sys, os, signal
import subprocess
import logging
import argparse, ConfigParser
from multiprocessing import Process, active_children
# from threading import Thread

import notify

def runInOtherThread(function, args):
    t = Process(target=function, args=args)
    t.start()

def checkChildren(sig, frame):
    active_children()

def signal_handler(sig, frame):
    logger.debug("job was cancelled by user at %s" % hostname)
    print("job was cancelled by user at %s" % hostname)
    process.terminate()
    sys.exit(0)

def signal_kill_handler(sig, frame):
    message = "job was kill at %s" % hostname
    logger.debug(message)
    notify.sendMail("job killed", message, "dspsr@pacifix")
    sys.exit(0)

def parseCommand(commandString):
    commands = commandString.split(",")
    return commands


def parseOptions():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', '-g', nargs=1, metavar="num", help='number of files procesesd together')
    parser.add_argument('--total', '-t', nargs=1, metavar="num", help="total parts")
    parser.add_argument('--part', '-p', nargs=1, metavar="num", help="part index")
    parser.add_argument('--job', '-j', nargs=1, metavar="jobFile", help="job file for the pipeline")
    parser.add_argument('--section', '-s', nargs=1, metavar="section", help="section name inside the job file")
    parser.add_argument('--continue', '-c', action="store_true", help="wether to continue on previous process")
    parser.add_argument('--thread', nargs=1, metavar="num", help="thread number, default: none")

    args = parser.parse_args()

    if None in (args.group, args.total, args.part, args.job, args.section):
        parser.error("insufficient arguments")

    return args

args = parseOptions()

section = args.section[0]

config = ConfigParser.ConfigParser()
config.read(args.job[0])
configItems = dict(config.items(section))
dataPath = configItems['data_path']
candiatePath = configItems['candidate_path']
intermediatePath = configItems['intermediate_path']
logPath = configItems['log_path']
pathPrefix = configItems['path_prefix']
instance = configItems['instance']
sendNotify = configItems['notify']
dataFileList = configItems.get('file_list', None)

commands = parseCommand(configItems['commands'])
# exit(0)
# commands = json.loads(configItems['commands'])


stackInterval = args.group[0]
thisPart = args.part[0]
totalParts = args.total[0]
outputPath = candiatePath + '/' + thisPart

timeConsistance = False
logsFileName = logPath + '/log'
if os.path.isfile(logsFileName):
    if os.path.getsize(logsFileName) > 2000000:
        os.rename(logsFileName, logsFileName + '.bak')
loggerFormat = '%(asctime)-15s  %(filename)s  %(message)s'
logging.basicConfig(filename=logsFileName , format = loggerFormat, level=logging.DEBUG)
logger = logging.getLogger(__name__)

hostname = os.uname()[1]

logger.debug("job started at %s with parameters %s" % (hostname + thisPart,
            " ".join([stackInterval, thisPart, totalParts, section])))
# if(not os.path.isdir(outputPath)):
    # os.mkdir(outputPath)
# os.chdir(outputPath)

if dataFileList is not None:
    with open(dataFileList, 'r') as fileListObj:
        allFiles = [line.strip() for line in fileListObj]
else:
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
if timeConsistance == True:
    currentTime = ''
    for dataFile in thisGroup:
        dataTime = dataFile.split('/')[-1].split('_')[0]
        if dataTime != currentTime:
            segments.append([])
            currentTime = dataTime
        segments[-1].append(dataFile)
else:
    segments = [thisGroup]

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_kill_handler)
signal.signal(signal.SIGCHLD, checkChildren)
retryCount = 0
processCount = 0
retryLimit = 10
sender = "gpsearch@numerix0"
if sendNotify == 'true':
    runInOtherThread(notify.sendWeb,
            (thisPart + "@gpsearch", "job {} started".format(section), instance))
for segment in segments:
    stackNum = len(segment)
    stackIdx = 0
    while stackIdx < stackNum:
        stackEnd = stackIdx + int(stackInterval)
        if stackEnd < stackNum:
            stackList = segment[stackIdx:stackEnd]
        else:
            stackList = segment[stackIdx:]
        stackIdx = stackEnd

        thisFileList = ' '.join(stackList)
        for command in commands:
            for attempt in range(retryLimit):
                cmd = command.format(thisFileList, intermediatePath,
                            candiatePath, pathPrefix, thisPart)
                process = subprocess.Popen(cmd,stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, shell=True)
                for line in iter(process.stdout.readline, ''):
                    sys.stdout.write(line)
                outs, errs = process.communicate()
                if process.returncode != 0:
                    message = "job exits unexpected at %s" % hostname
                    logger.debug(message)
                    logger.debug(errs)
                    logger.debug("retry the command")
                    print(errs)
                else:
                    '''files are successfully procesesd.'''
                    break
            else:
                message = ("max retry reached, skip files: %s at %s"
                          "with command: %s") % (thisFileList, hostname, command)
                logger.debug(message)
                runInOtherThread(notify.sendMail, ("job skipped", message, sender))
                break
        processCount += len(stackList)
        message = ("procesesd: {}, remain: {}".format(
                    processCount, len(thisGroup) - processCount))
        if sendNotify == 'true':
            runInOtherThread(notify.sendWeb, (thisPart + "@gpsearch", message, instance))
        print(message)

message = ("job stopped at %s after processing %d files "
          "with parameters %s and command: %s ") % (
            hostname, processCount," ".join([stackInterval, thisPart, totalParts, section]), " ".join(commands))
logger.debug(message)
if sendNotify == 'true':
    notify.sendMail("job stopped", message, sender)
    runInOtherThread(notify.sendWeb,
            (thisPart + "@gpsearch", "job {} stopped".format(section), instance))

