#!/bin/bash

#カレントディレクトリを取得
CDIR=`pwd`

#保存先ディレクトリをコマンドライン引数（１番目）から取得
DIRNAME=${1}
FLG=${2}

#作業デレクトリを画像保存先に変更
cd ${DIRNAME}

#dcrawによるtiff変換
case "$FLG" in
	  "2") echo gamma 2.4
				 dcraw -v -T -g 2.4 12.92 -W *.DNG
	       ;;
	  "3") echo gamma 2.4 output XYZ data
				 dcraw -v -T -g 2.4 12.92 -W *.DNG
	       ;;
	  "4") echo gamma 1.0 output RGB data
				 dcraw -v -T -g 1 1 -W *.DNG
		   ;;
	  "5") echo gamma 2.4 output RGB data
				 dcraw -v -T -g 2.4 12.92 -W *.DNG
	       ;;
	  *)   echo gamma 1.0
		     dcraw -v -T -g 1 1 -W *.DNG
	       ;;
esac
echo raw to tiff convert done.


#作業デレクトリをもとに戻す
cd ${CDIR}

#pythonスクリプトでXYZ変換
case "$FLG" in
		"2") echo gamma 2.4
				 python3 conv_hdr_xyz.py -i ${DIRNAME} -g 2
				 ;;
		"3") echo gamma 2.4 output XYZ data 
				 python3 conv_hdr_xyz.py -i ${DIRNAME} -g 2 -o 3
				 ;;
		"4") echo gamma 1.0 output RGB data
				 python3 conv_hdr_xyz.py -i ${DIRNAME} -t 2
				 ;;
		"5") echo gamma 2.4 output RGB data 
				 python3 conv_hdr_xyz.py -i ${DIRNAME} -g 2 -t 2
				 ;;
		*)   echo gamma 1.0
		     python3 conv_hdr_xyz.py -i ${DIRNAME}
				 ;;
esac
