import cv2
import argparse
import matplotlib.pyplot as plt

#main() 
#imagesのディレクトリ指定
parser = argparse.ArgumentParser(description='Code for Image Viewer.')
parser.add_argument('--input', type=str, help='Path to the image file.')
args = parser.parse_args()
if not args.input:
    parser.print_help()
    exit(0)
 
#画像の読み込み       
img = cv2.imread(args.input)

#画像の表示
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.show()



