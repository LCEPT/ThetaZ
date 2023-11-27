import numpy as np
import argparse
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import matplotlib.gridspec as gridspec
from numba import jit
import cv2
import math
import os
os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"

##### GLOBAL VARIABLES AND CONSTANTS#####
#fisheye center
c1_x = 1824
c1_y = 1824
c2_x = 5472
c2_y = 1824
#input image size
IMGi_H = 3648
IMGi_W = 3648 
IMGi_R = 1725
#output image size
IMGo_H = 3450
IMGo_W = 3450 
IMGo_R = 1725

def loadLuminanceFile(path):
    ext = os.path.splitext(os.path.basename(path))[1][1:]
    if ext == 'csv':
        matY = np.genfromtxt(
            fname=path,
            dtype="float",
            delimiter=","
        )
    elif ext == 'exr':
        hdrImg = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        matY =  hdrImg[:,:,1]
    return matY

#transform to Equidistant Cylindrical Projection from Equisolidangle Projection
@jit(nopython=True)
def trans_EDC_img(inimg):
    print("converting ESA image to EDC image.")
    outimg = np.zeros((IMGo_H, IMGo_W))
    for po in range(IMGo_H):
        for qo in range(IMGo_W):
            #Convert to a coordinate system centered on the optical axis
            xo = qo - IMGo_W/2
            yo = IMGo_H/2 - po
            #Convert to azimuth and elevation angle[rad]
            theta = xo * math.pi / IMGo_W
            phi   = yo * math.pi / IMGo_H
            #Calculation of spherical coordinates
            x_sph = IMGi_R * math.cos(phi) * math.sin(theta)
            y_sph = IMGi_R * math.sin(phi)
            z_sph = IMGi_R * math.cos(phi) * math.cos(theta)
            #coordinate transformation
            if xo ==0 and yo == 0:
                outimg[po,qo]=inimg[int(IMGi_H/2), int(IMGi_W/2)]
            else:
                #Calculate the coordinates of the input data
                xi = IMGi_R * math.sqrt(1 - z_sph/IMGi_R) * x_sph/math.sqrt(x_sph**2+y_sph**2)
                yi = IMGi_R * math.sqrt(1 - z_sph/IMGi_R) * y_sph/math.sqrt(x_sph**2+y_sph**2)
                pi = math.floor(IMGi_H/2 - yi)
                qi = math.floor(xi + IMGi_W/2)
                dp = (IMGi_H/2 - yi) - pi
                dq = (xi + IMGi_W/2) - qi
                #Bilinear interpolation with the values of 4 pixels around the original coordinates
                if pi >= IMGi_H-1 and qi >= IMGi_W-1:
                    val_0_0 = inimg[pi, qi]
                    val_0_1 = 0
                    val_1_0 = 0
                    val_1_1 = 0
                    outimg[po,qo] = val_0_0
                elif pi >= IMGi_H-1:
                    val_0_0 = inimg[pi, qi]
                    val_0_1 = inimg[pi, qi + 1]
                    val_1_0 = 0
                    val_1_1 = 0
                    outimg[po,qo] = val_0_0 + (val_0_1 - val_0_0)*dq
                elif qi >= IMGi_W-1:
                    val_0_0 = inimg[pi, qi]
                    val_0_1 = 0
                    val_1_0 = inimg[pi + 1, qi]
                    val_1_1 = 0
                    outimg[po,qo] = val_0_0 + (val_1_0 - val_0_0)*dp
                else:
                    val_0_0 = inimg[pi, qi]
                    val_0_1 = inimg[pi, qi + 1]
                    val_1_0 = inimg[pi + 1, qi]
                    val_1_1 = inimg[pi + 1, qi + 1]
                    outimg[po,qo]=(1-dq)*(1-dp)*val_0_0 \
                                 + dq*(1-dp)*val_0_1 \
                                 + (1-dq)*dp*val_1_0 \
                                 + dq*dp*val_1_1
    print("convert done.")
    return outimg

#Generate the Lens correction matrix
@jit(nopython=True)
def cut_boundary(img):
    h, w = img.shape
    mat_bnd = np.zeros((h , w))
    for i in range(h):
        for j in range(w):
            p = c1_y - i
            q = c1_x - j
            d = math.sqrt(p*p + q*q)
            if d < IMGo_R:
                mat_bnd[i, j] = 1
            else:
                mat_bnd[i, j] = 0
    r_mat = img*mat_bnd
    r_mat = r_mat[99:3549, 99:3549]
    return r_mat




##### Main() #####



parser = argparse.ArgumentParser(description='Code for Pseudo Color Imaging tutorial.')
parser.add_argument('-i', '--input', required=True, type=str, help='Path to the file that contains luminance values.')
args = parser.parse_args()
if not args.input:
    parser.print_help()
    exit(0)

#輝度CSVファイルの読み込み
print('Loding csv data...')
matY = loadLuminanceFile(args.input)
print('done')

#輝度csvファイルの分離
ESA_matY_F = matY[:, 3648:]
ESA_matY_B = matY[:, :3648]
ESA_matY_F = np.where(ESA_matY_F>0, ESA_matY_F, np.nan)
ESA_matY_B = np.where(ESA_matY_B>0, ESA_matY_B, np.nan)
ESA_matY = np.concatenate([ESA_matY_F, ESA_matY_B], 1)

#Transform to Equi-Distant Cylindrical Projection from Equi-Solid-Angle Projection
EDC_matY_F = trans_EDC_img(ESA_matY_F)
EDC_matY_B = trans_EDC_img(ESA_matY_B)
EDC_matY  = np.concatenate([EDC_matY_F,EDC_matY_B], axis=1) 

ESA_matY_F_trim = cut_boundary(ESA_matY_F) 
ESA_matY_B_trim = cut_boundary(ESA_matY_B) 

#0をNaNで置換
ESA_matY_F_trim = np.where(ESA_matY_F_trim>0, ESA_matY_F_trim, np.nan)
ESA_matY_B_trim = np.where(ESA_matY_B_trim>0, ESA_matY_B_trim, np.nan)

#ヒストグラムファイル名
h_file = os.path.dirname(args.input) + "/hist_L.csv"

#グラフ描画
fig = plt.figure(figsize=(6,9))
fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.05, hspace=0.05)
gs = gridspec.GridSpec(3,2,figure=fig)

ax0 = fig.add_subplot(gs[0,:])
mappable0 = ax0.imshow(EDC_matY, cmap='jet', norm=LogNorm(vmin=1e-3, vmax=1e6))
ax0.axis("off")

ax1 = fig.add_subplot(gs[1,0])
mappable1 = ax1.imshow(ESA_matY_F_trim, cmap='jet', norm=LogNorm(vmin=1e-3, vmax=1e6))
ax1.axis("off")
ax2 = fig.add_subplot(gs[1,1])
mappable2 = ax2.imshow(ESA_matY_B_trim, cmap='jet', norm=LogNorm(vmin=1e-3, vmax=1e6))
ax2.axis("off")

ax3 = fig.add_subplot(gs[2,0])
ax4 = fig.add_subplot(gs[2,1])

n1, bins1, patches1 = ax3.hist(ESA_matY_F_trim.flatten(), bins=np.logspace(-3,6,100), color='silver', alpha=0.75)
ax3.set_xscale('log')
ax3.set_xlim(1e-3, 1e6)
ax3.xaxis.set_visible(False)
ax3.tick_params('x', labelsize = 0)
ax3.set_yscale('log')
ax3.set_ylabel('num')

n2, bins2, patches2 = ax4.hist(ESA_matY_B_trim.flatten(), bins=np.logspace(-3,6,100), color='silver', alpha=0.75)
ax4.set_xscale('log')
ax4.set_xlim(1e-3, 1e6)
ax4.xaxis.set_visible(False)
ax4.tick_params('x', labelsize = 0)
ax4.set_yscale('log')
ax4.set_ylabel('num')
ax4.tick_params(labelbottom=True, labelleft=False, labelright=False, labeltop=False)

Amean1 = np.nansum(ESA_matY_F_trim)/(np.count_nonzero(ESA_matY_F_trim>0))  #算術平均輝度の算出
maxLumi1=np.nanmax(ESA_matY_F_trim)
minLumi1=np.nanmin(ESA_matY_F_trim[np.nonzero(ESA_matY_F_trim)])
#Gmean=geo_mean(matY.flatten())
Amean2 = np.nansum(ESA_matY_B_trim)/(np.count_nonzero(ESA_matY_B_trim>0))  #算術平均輝度の算出
maxLumi2=np.nanmax(ESA_matY_B_trim)
minLumi2=np.nanmin(ESA_matY_B_trim[np.nonzero(ESA_matY_B_trim)])

pp1 = fig.colorbar(mappable1, ax = ax3, orientation="horizontal", pad=0)
#pp1.set_clim(1e-3, 1e6)
pp1.set_label("Luminance [cd/m2]", fontsize=10)

pp2 = fig.colorbar(mappable2, ax = ax4, orientation="horizontal", pad=0)
#pp2.set_clim(1e-3, 1e6)
pp2.set_label("Luminance [cd/m2]", fontsize=10)

#plt.suptitle(args.input)

with open(h_file, "w") as fileobj:
    fileobj.write(str(os.path.dirname(args.input)) + ",\n")
    fileobj.write("表面,\n")
    fileobj.write("算術平均輝度,最大輝度,最小輝度,\n")
    fileobj.write(str(Amean1) + "," + str(maxLumi1) + "," + str(minLumi1) + ",\n")
    fileobj.write("階級,ピクセル数,\n")
    for i in range(0, len(bins1)):
        if i == len(bins1)-1:
            fileobj.write(str(bins1[i]) + ",-,\n")
        else:
            fileobj.write(str(bins1[i]) + "," + str(n1[i]) + "\n")

    fileobj.write("裏面,\n")
    fileobj.write("算術平均輝度,最大輝度,最小輝度,\n")
    fileobj.write(str(Amean2) + "," + str(maxLumi2) + "," + str(minLumi2) + ",\n")
    fileobj.write("階級,ピクセル数２,\n")
    for i in range(0, len(bins2)):
        if i == len(bins2)-1:
            fileobj.write(str(bins2[i]) + ",-,\n")
        else:
            fileobj.write(str(bins2[i]) + "," + str(n2[i]) + "\n")

plt.show()
