import numpy as np
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
matR = np.genfromtxt(
    fname = os.path.join(args.input, 'dataR.csv'),
    dtype = "float",
    delimiter = ","
)
matG = np.genfromtxt(
    fname = os.path.join(args.input, 'dataG.csv'),
    dtype = "float",
    delimiter = ","
)
matB = np.genfromtxt(
    fname = os.path.join(args.input, 'dataB.csv'),
    dtype = "float",
    delimiter = ","
)

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
    
