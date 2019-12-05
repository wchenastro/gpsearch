#!/usr/bin/env python

import sys, csv
import argparse


if len(sys.argv) < 2 + 1:
    print("insufficient arguments")
    exit(-1)


inputFile = sys.argv[1]
outputFile = sys.argv[2]
parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', nargs=1, metavar="filename", help='input candidate file')
parser.add_argument('--output', '-o', nargs=1, metavar="filename", help='refined candidate file')
parser.add_argument('--width', '-w', nargs=1, metavar="filename", help='maximum width of the pulse')
parser.add_argument('--cluster', '-c', nargs=1, metavar="filename", help='maximum width of the pulse')

args = parser.parse_args()

pulseStart = 7
pulseEnd = 8
DMCluster = 6
width = float(args.width[0])
DMClusterMin = float(args.cluster[0])

refinedCands = []
with open(args.input[0]) as csvFile:
    reader = csv.reader(csvFile, delimiter='\t')
    for row in reader:
        if ((float(row[pulseEnd]) - float(row[pulseStart])) > width):
            continue
        if(float(row[DMCluster]) < DMClusterMin):
            continue
        refinedCands.append(row)

with open(args.output[0], 'w') as csvFile:
    writer = csv.writer(csvFile, delimiter='\t')
    writer.writerows(refinedCands)
