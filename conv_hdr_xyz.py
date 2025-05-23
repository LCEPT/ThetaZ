## Last update 2025/05/06
## L-CEPT v1.3.0

import OpenEXR
import Imath
import numpy as np
import argparse
import csv
import os
import math
import time
from numba import jit
os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
import cv2
from fractions import Fraction
import warnings

#For writing header information
SOFTWARE_V = "L-CEPT v1.3.0"
LOCALTIME = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
UTC = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
FORMAT = None
CAMERA_ID = None
LENS_ID = None
FISHEYE_R = None

#Load images and integration
def makeHDRimage(path, g_flag):
    #initialize matrix
    hdr_img = []
    summed_Rimg = np.zeros((imgH, imgW), dtype='float16')
    summed_Gimg = np.zeros((imgH, imgW), dtype='float16')
    summed_Bimg = np.zeros((imgH, imgW), dtype='float16')
    total_Rimg = np.zeros((imgH, imgW), dtype='int8')
    total_Gimg = np.zeros((imgH, imgW), dtype='int8')
    total_Bimg = np.zeros((imgH, imgW), dtype='int8')
    
    #Loop for the number of images
    with open(os.path.join(path, 'picInfo.csv')) as f:
        content = f.readlines()
    for line in content:
        #Load image and EV values
        tokens = line.split(',')
        print(tokens[1], 'load image and convert')
        img = cv2.imread(os.path.join(path, tokens[1]))
        ev = 1/(float(tokens[2])*float(Fraction(tokens[3])))
        #Blue ch
        if g_flag == 1:
            img_b = np.where( (img[:,:,0]>TH_H) | (img[:,:,0]<TH_L), 0, img[:,:,0] )
        elif g_flag == 2:
            img_b = np.where( (img[:,:,0]>TH_H) | (img[:,:,0]<TH_L), 0, img[:,:,0]/255 )
            img_b = np.where( img_b[:,:]>0.04045, ((img_b[:,:]+0.055)/1.055)**(2.4), img_b[:,:]/12.92 )
        cnt_b = np.where( (img[:,:,0]>TH_H) | (img[:,:,0]<TH_L), 0, 1 )
        summed_Bimg = summed_Bimg + ev*img_b
        total_Bimg  = total_Bimg + cnt_b
        #Green ch
        if g_flag ==1:
            img_g = np.where( (img[:,:,1]>TH_H) | (img[:,:,1]<TH_L), 0, img[:,:,1] )
        elif g_flag == 2:
            img_g = np.where( (img[:,:,1]>TH_H) | (img[:,:,1]<TH_L), 0, img[:,:,1]/255 )
            img_g = np.where( img_g[:,:]>0.04045, ((img_g[:,:]+0.055)/1.055)**(2.4), img_g[:,:]/12.92 )
        cnt_g = np.where( (img[:,:,1]>TH_H) | (img[:,:,1]<TH_L), 0, 1 )
        summed_Gimg = summed_Gimg + ev*img_g
        total_Gimg  = total_Gimg + cnt_g
        #Red ch
        if g_flag == 1:
            img_r = np.where( (img[:,:,2]>TH_H) | (img[:,:,2]<TH_L), 0, img[:,:,2] )
        elif g_flag == 2:
            img_r = np.where( (img[:,:,2]>TH_H) | (img[:,:,2]<TH_L), 0, img[:,:,2]/255 )
            img_r = np.where( img_r[:,:]>0.04045, ((img_r[:,:]+0.055)/1.055)**(2.4), img_r[:,:]/12.92 )
        cnt_r = np.where( (img[:,:,2]>TH_H) | (img[:,:,2]<TH_L), 0, 1 )
        summed_Rimg = summed_Rimg + ev*img_r
        total_Rimg  = total_Rimg + cnt_r
    #calculating the average value for each pixel
    summed_Rimg = np.divide(summed_Rimg, total_Rimg, out=np.zeros_like(summed_Rimg), where=total_Rimg!=0)
    summed_Gimg = np.divide(summed_Gimg, total_Gimg, out=np.zeros_like(summed_Gimg), where=total_Gimg!=0)
    summed_Bimg = np.divide(summed_Bimg, total_Bimg, out=np.zeros_like(summed_Bimg), where=total_Bimg!=0)
    hdr_img.append(summed_Bimg)
    hdr_img.append(summed_Gimg)
    hdr_img.append(summed_Rimg)
    return hdr_img

#Generate the Lens correction matrix
@jit(nopython=True)
def makeLensMatrix(h,w,r,x1,y1,x2,y2):
    matLens = np.zeros((h,w))
    for i in range(h):
        for j in range(w):
            if j < w/2:
                p = y1 - i
                q = x1 - j
                d = math.sqrt(p*p + q*q)
                if d < w/2:
                    matLens[i, j] = 1
                else:
                    matLens[i, j] = 0
            else:
                p = y2 - i
                q = x2 - j
                d = math.sqrt(p*p + q*q)
                if d < w/2:
                    matLens[i, j] = 1
                else:
                    matLens[i, j] = 0
    return matLens


###main()################    
#Command Line Argument Definitions
parser = argparse.ArgumentParser(description='Code for convert rgb image to xyz value.')
parser.add_argument('-i', '--input', required=True, type=str, help='Path to the directory that contains images and "sysInfo*.csv".')
parser.add_argument('-s', '--system', type=str, default='sysInfo.csv', help='Input the file name of "sysInfo*.csv".')
parser.add_argument('-o', '--option', type=int, default=1, help='1:Output XYZ EXR file. (default), 2:Output Y value  CSV file only., 3:Output RGB EXR file.')
parser.add_argument('-g', '--gamma', type=int, default=1, help='1:Input images with gamma value of 1.0. (default), 2:Input images with sRGB standard.')
args = parser.parse_args()

#Parse command line arguments
if not args.input:
    parser.print_help()
    exit(0)
#Load system setup file
with open(os.path.join(args.input, args.system), 'r') as f:
    reader = csv.reader(f)
    line = [row for row in reader]
#print sysInfo header
print(line[0])
print(line[1])
print(line[2])
print(line[3]) 
CAMERA_ID = line[0][1]
LENS_ID = line[1][1]
### variables setting ##############
#fisheye center
c1_x = 1824
c1_y = 1824
c2_x = 5472
c2_y = 1824
#image size
imgH = int(line[4][1]) 
imgW = int(line[5][1]) 
#fisheye radius
imgR = int(line[6][1])
FISHEYE_R = imgR 
#conversion matrix
RX = float(line[7][1]) 
GX = float(line[8][1]) 
BX = float(line[9][1]) 
RY = float(line[10][1]) 
GY = float(line[11][1]) 
BY = float(line[12][1]) 
RZ = float(line[13][1]) 
GZ = float(line[14][1]) 
BZ = float(line[15][1])
#Range of RGB values to convert
TH_H = int(line[16][1]) 
TH_L = int(line[17][1]) 
####################################


#Load images and integration
start_t =time.time()
print('making HDR image...')
hdr = makeHDRimage(args.input, args.gamma)
load_end_t = time.time()
t01 = load_end_t - start_t
print("done. {:.2f} [sec]".format(t01))


#initialize matrix
print('matrix initialize...')
if args.option == 1 or args.option == 2:
    matX = np.zeros((imgH,imgW), dtype='float16')
    matY = np.zeros((imgH,imgW), dtype='float16')
    matZ = np.zeros((imgH,imgW), dtype='float16')
elif args.option ==3:
    matR = np.zeros((imgH,imgW), dtype='float16')
    matG = np.zeros((imgH,imgW), dtype='float16')
    matB = np.zeros((imgH,imgW), dtype='float16')   
#Lens correction
matLens = makeLensMatrix(imgH, imgW, imgR, c1_x, c1_y, c2_x, c2_y)
m_init_t = time.time()
t02 = m_init_t - load_end_t
print("done. {:.2f} [sec]".format(t02))


#convert RGB to XYZ
print('convert RGB...')
if args.option == 1:
    if args.gamma == 1:
        matX = RX * hdr[2] + GX * hdr[1] + BX * hdr[0]
        matY = RY * hdr[2] + GY * hdr[1] + BY * hdr[0]
        matZ = RZ * hdr[2] + GZ * hdr[1] + BZ * hdr[0]
    elif args.gamma == 2:
        matX = 255*(RX * hdr[2] + GX * hdr[1] + BX * hdr[0])
        matY = 255*(RY * hdr[2] + GY * hdr[1] + BY * hdr[0])
        matZ = 255*(RZ * hdr[2] + GZ * hdr[1] + BZ * hdr[0])
    #triming of minmum XYZvalues
    matX = np.where(matX<0.001, 0.001, matX)
    matY = np.where(matY<0.001, 0.001, matY)
    matZ = np.where(matZ<0.001, 0.001, matZ)
    #triming of FElens
    matX_trim = matX*matLens
    matY_trim = matY*matLens
    matZ_trim = matZ*matLens
    matXYZ = cv2.merge((matZ_trim, matY_trim, matX_trim))
elif args.option == 2:
    if args.gamma == 1:
        matY = RY * hdr[2] + GY * hdr[1] + BY * hdr[0]
    elif args.gamma == 2:
        matY = 255*(RY * hdr[2] + GY * hdr[1] + BY * hdr[0])
    matY = np.where(matY<0.001, 0.001, matY)
elif args.option == 3:
    if args.gamma == 1:
        matR = hdr[2]*matLens
        matG = hdr[1]*matLens
        matB = hdr[0]*matLens
    elif args.gamma == 2:
        matR = 255*hdr[2]*matLens
        matG = 255*hdr[1]*matLens
        matB = 255*hdr[0]*matLens
    matRGB = cv2.merge((matB, matG, matR))
conv_done_t = time.time()
t03 = conv_done_t - m_init_t
print("done. {:.2f} [sec]".format(t03))


#Output data files
print('saving files...')
if args.option == 1:
    # XYZ チャネルを分離 (OpenCV のチャネル順：0=Z,1=Y,2=X)
    chan_Z, chan_Y, chan_X = cv2.split(matXYZ)
    # half precision (float16) にキャスト
    with warnings.catch_warnings():
        warnings.simplefilter("ignore",RuntimeWarning)
        chan_X = chan_X.astype(np.float16)  # numpy の float16
        chan_Y = chan_Y.astype(np.float16)
        chan_Z = chan_Z.astype(np.float16)
    # チャネル辞書 (numpy 配列をそのまま渡す)
    channels = {
        'X': chan_X,
        'Y': chan_Y,
        'Z': chan_Z
    }
    #CONVERSION_FACTOR = [RX,GX,BX,RY,GY,BY,RZ,GZ,BZ] 
    #print(CONVERSION_FACTOR)
    # ヘッダ辞書 (基本型をそのまま渡すだけ)
    header = {
        'compression'       : OpenEXR.ZIP_COMPRESSION,
        'type'              : OpenEXR.scanlineimage,
        'FORMAT'            : "XYZ 16-bit float",
        'CAMERA'            : CAMERA_ID,
        'LENS'              : LENS_ID,
        'FISHEYE_RADIUS'    : FISHEYE_R,
        'GAMMA'             : "1.0" if args.gamma == 1 else "sRGB",
        'CONVERSION_FACTOR' : "{}".format(' '.join(f"{v:.6f}" for v in [RX, GX, BX, RY, GY, BY, RZ, GZ, BZ])),
        'LOCALTIME'         : LOCALTIME,   # 例: "2025-04-22T09:30:00+09:00"
        'GMT'               : UTC,         # 例: "2025-04-22T00:30:00Z"
        'SOFTWARE_V'        : SOFTWARE_V
    }
    # 出力ファイルパス
    output_path = os.path.join(args.input, 'dataXYZ.exr')
    # 新 API で書き出し
    with OpenEXR.File(header, channels) as exr:
        exr.write(output_path)
    print("EXR file saved to", output_path)
    
elif args.option == 2:
    np.savetxt(os.path.join(args.input, 'dataY.csv'), matY, delimiter=",", fmt='%.3f')
    
elif args.option == 3:
    # Option 3: RGB EXRファイルとして保存する例
    # RGB チャネルを分離 (OpenCV のチャネル順：0=B,1=G,2=R)
    chan_B, chan_G, chan_R = cv2.split(matRGB)
    # half precision (float16) にキャスト
    with warnings.catch_warnings():
        warnings.simplefilter("ignore",RuntimeWarning)
        chan_R = chan_R.astype(np.float16)  # numpy の float16
        chan_G = chan_G.astype(np.float16)
        chan_B = chan_B.astype(np.float16)
    # チャネル辞書 (numpy 配列をそのまま渡す)
    channels = {
        'R': chan_R,
        'G': chan_G,
        'B': chan_B
    }
    # ヘッダ辞書 (基本型をそのまま渡すだけ)
    header = {
        'compression'       : OpenEXR.ZIP_COMPRESSION,
        'type'              : OpenEXR.scanlineimage,
        'FORMAT'            : "RGB 16-bit float",
        'CAMERA'            : CAMERA_ID,
        'LENS'              : LENS_ID,
        'FISHEYE_RADIUS'    : FISHEYE_R,
        'GAMMA'             : "1.0" if args.gamma == 1 else "sRGB",
        'LOCALTIME'         : LOCALTIME,   # 例: "2025-04-22T09:30:00+09:00"
        'GMT'               : UTC,         # 例: "2025-04-22T00:30:00Z"
        'SOFTWARE_V'        : SOFTWARE_V
    }
    # 出力ファイルパス
    output_path = os.path.join(args.input, 'dataRGB.exr')
    # 新 API で書き出し
    with OpenEXR.File(header, channels) as exr:
        exr.write(output_path)
    print("EXR file saved to", output_path)
