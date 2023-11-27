#!/bin/bash

#カレントディレクトリを取得
CDIR=`pwd`
#保存先ディレクトリをコマンドライン引数（１番目）から取得
DIRNAME=${1}
FLG=${2}

#画像保存先フォルダを読み込み現像
while read -r line
do
	#作業デレクトリを画像保存先に変更
	col1=`echo ${line} | cut -d ',' -f 1`
	dir_data=`basename ${col1}`
	cd ${DIRNAME}/${dir_data}
	#dcrawによるtiff変換
	case "$FLG" in
	"11") echo gamma 1.0 output XYZ data
		dcraw -v -T -g 1 1 -W *.DNG
		;;
	"12") echo gamma 2.4 output XYZ data
		dcraw -v -T -g 2.4 12.92 -W *.DNG
		;;
	"21") echo gamma 1.0 output Y data
		dcraw -v -T -g 1 1 -W *.DNG
		;;
	"22") echo gamma 2.4 output Y data
		dcraw -v -T -g 2.4 12.92 -W *.DNG
		;;
	"31") echo gamma 1.0 output RGB data
		dcraw -v -T -g 1 1 -W *.DNG
		;;
	"32") echo gamma 1.0 output RGB data
		dcraw -v -T -g 2.4 12.92 -W *.DNG
		;;
	*)   echo gamma 1.0 output XYZ data
		dcraw -v -T -g 1 1 -W *.DNG
		;;
	esac
	echo raw to tiff convert done.
	cd ${CDIR}
	#pythonスクリプトでXYZ変換
	case "$FLG" in
	"11") echo gamma 1.0 output XYZ data
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -o 1 -g 1
		;;
	"12") echo gamma 2.4 output XYZ data
		pythyon3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -o 1 -g 2
		;;
	"21") echo gamma 1.0 output Y data
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -o 2 -g 1
		;;
	"22") echo gamma 2.4 output XYZ data 
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -g 2 -o 2
		;;
	"31") echo gamma 1.0 output RGB data
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -g 3 -o 1
		;;
	"32") echo gamma 2.4 output RGB data 
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -g 2 -o 2
		;;
	*)   echo gamma 1.0 output XYZ data
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data}
		;;
	esac
done < ${DIRNAME}/dirList.txt


#作業デレクトリをもとに戻す
cd ${CDIR}
