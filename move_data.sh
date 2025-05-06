#!/bin/bash

#カレントディレクトリを取得
CDIR=`pwd`
#保存ディレクトリをコマンドライン引数（１番目）から取得
DIRNAME=${1}
#移動先のディレクトリをコマンドライン引数（2番目）から取得
MOVEDIR=${2}

#画像保存先フォルダを読み込み現像
while read -r line
do
	#作業デレクトリを画像保存先に変更
	col1=`echo ${line} | cut -d ',' -f 1`
	dir_data=`basename ${col1}`
	cd ${DIRNAME}/${dir_data}
	#撮影時のsysInfoを画像フォルダにコピー
    cp dataXYZ.exr ${MOVEDIR}/${dir_data}_dataXYZ.exr
    
done < ${DIRNAME}/dirList.txt


#作業デレクトリをもとに戻す
cd ${CDIR}
