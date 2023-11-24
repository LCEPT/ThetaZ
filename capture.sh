#!/bin/bash

#保存先の親ディレクトリをコマンドライン引数から取得
DIRNAME=${1}

#保存先ディレクトリの作成
DATE=`date '+%y%m%d_%H%M%S'`
mkdir ${DIRNAME}/${DATE}
chmod 777 ${DIRNAME}/${DATE}

#Thetaの設定可能なプロパティは以下のURL参考
# https://github.com/ricohapi/theta-api-specs/tree/main/theta-usb-api

#カメラのアクティベート
ptpcam -i
sleep 1.0
ptpcam -i
#露光モードをマニュアルに変更
ptpcam --set-property=0x500e --val=0x0001
sleep 0.1
#シャッター時の音声調整
ptpcam --set-property=0x502c --val=20
sleep 0.1
#画像サイズを指定
ptpcam --set-property=0x5003 --val=6720x3360
sleep 0.1
#RAW画像取得をON
ptpcam --set-property=0xD827 --val=0x01
sleep 0.1
#ホワイトバランスの設定
ptpcam --set-property=0x5005 --val=0x8002
sleep 0.1
#絞りの設定
ptpcam --set-property=0x5007 --val=560
sleep 0.1
#スリープ機能をOFF
ptpcam --set-property=0xd803 --val=0
sleep 0.1
#前撮影画像の削除
ptpcam -D
sleep 0.1

#ループ回数カウント
cnt=0
#露光時間 ISO感度を変えて撮影
while read -r line
do
	cnt=`expr $cnt + 1`
	col1=`echo ${line} | cut -d ',' -f 1`
	col2=`echo ${line} | cut -d ',' -f 2`
	col3=`echo ${line} | cut -d ',' -f 3`
	col4=`echo ${line} | cut -d ',' -f 4`
	col5=`echo ${line} | cut -d ',' -f 5`
	col6=`echo ${line} | cut -d ',' -f 6`
	ptpcam --set-property=0x500f --val=${col4}
	echo -e -n ${col5} > val.bin
	ptpcam -R 0x1016,0xd00f,0,0,0,0,val.bin
	echo
	echo //// Getting Image of ${col1} ////
	sleep 0.1
	ptpcam -c
	sleep ${col6}
	echo ${col1}.DNG,${col1}.tiff,${col2},${col3} >> ${DIRNAME}/${DATE}/picInfo.csv
done < ${DIRNAME}/EVlist.csv
#list.csvの書式
#１列目　画像No.
#２列目　ISO感度
#３列目　シャッタースピード
#４列目　ISO感度（１６進）
#５列目　シャッタースピード（１６進）
#６列目　画像取得待ち時間（シャッタースピードの２倍程度）

#画像のダウンロード
gphoto2 --auto-detect
gphoto2 -P
sudo chmod 777 *.DNG
sudo chmod 777 *.JPG
#画像のリネーム
ls *.DNG | awk '{ printf "mv %s %02d.DNG\n", $0, NR }' | sh
ls *.JPG | awk '{ printf "mv %s %02d.JPG\n", $0, NR }' | sh
#画像の移動
mv *.DNG ${DIRNAME}/${DATE}/
mv *.JPG ${DIRNAME}/${DATE}/
#撮影時のsysInfoを画像フォルダにコピー
cp ${DIRNAME}/sysInfo.csv ${DIRNAME}/${DATE}/sysInfo.csv
#画像の削除
ptpcam -i
sleep 1.0
ptpcam -i
ptpcam -D
#保存された画像枚数の確認
npic=`find ${DIRNAME}/${DATE} -name "*.DNG" | wc -l`
if [ $cnt -eq $npic ]; then
	#保存先ディレクトリの書き出し
	echo ${DIRNAME}/${DATE}, >> ${DIRNAME}/dirList.txt
else
	#撮影のやり直し
	sudo ./capture.sh ${1}
fi

