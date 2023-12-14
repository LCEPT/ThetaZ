import numpy as np
import cv2
import argparse
import os
    
#main() 
#input the location of CSV files
parser = argparse.ArgumentParser(description='Code for pick up RGB values.')
parser.add_argument('--input', type=str, help='Path to the RGB csv file.')
args = parser.parse_args()
if not args.input:
    parser.print_help()
    exit(0)
 
#Load RGB CSV files
with open(os.path.join(args.input, 'point.csv')) as f:
        content = f.readlines()  
print(len(content))
rgb_vals = []

hdrImg = cv2.imread(os.path.join(args.input, 'dataRGB.exr'), cv2.IMREAD_UNCHANGED)

matR = hdrImg[:,:,2]
matG = hdrImg[:,:,1]
matB = hdrImg[:,:,0]

#getting RGB values
for line in content:
    tokens = line.split(',')
    row = int(tokens[0])
    col = int(tokens[1])
    step = int(tokens[2])
    r = matR[col-step:col+step, row-step:row+step].mean()
    g = matG[col-step:col+step, row-step:row+step].mean()
    b = matB[col-step:col+step, row-step:row+step].mean()
    rgb = (r, g, b)
    rgb_vals.append(rgb)
    
np.savetxt(os.path.join(args.input,'rgb_vals.csv'), rgb_vals, delimiter=",", fmt='%f')
    
