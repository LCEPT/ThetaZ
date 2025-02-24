#!/bin/bash

#保存先の親ディレクトリをコマンドライン引数（1番目）から取得
DIRNAME=${1}

#撮影後の動作をコマンドライン引数（2番目）から取得
FLG=${2}

# ディレクトリの属するファイルシステムの使用容量を取得
USE_PERCENT=$(df "$DIRNAME" | awk 'NR==2 {gsub("%",""); print $5}')

# 使用容量が90%以上の場合に警告を表示して終了
if [ "$USE_PERCENT" -ge 90 ]; then
    echo "Warning: There is insufficient storage space at the destination. Please change the destination or ensure sufficient capacity."
    exit 1
fi

#保存先ディレクトリの作成
DAY=`date '+%y%m%d'`
TIME=`date '+%H%M%S'`
mkdir -p ${DIRNAME}/${DAY}
chmod 777 ${DIRNAME}/${DAY}
mkdir ${DIRNAME}/${DAY}/${TIME}
chmod 777 ${DIRNAME}/${DAY}/${TIME}

#カメラのアクティベート
ptpcam -i
sleep 1.0
ptpcam -i
#露光モードをマニュアルに変更
ptpcam --set-property=0x500e --val=0x0001
sleep 0.1
#シャッター時の音声調整
ptpcam --set-property=0x502c --val=0
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
#余分な画像を削除
ptpcam -D



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
	echo ${col1}.DNG,${col1}.tiff,${col2},${col3} >> ${DIRNAME}/${DAY}/${TIME}/picInfo.csv
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
mv *.DNG ${DIRNAME}/${DAY}/${TIME}/
mv *.JPG ${DIRNAME}/${DAY}/${TIME}/
#撮影時のsysInfoを画像フォルダにコピー
cp ${DIRNAME}/sysInfo* ${DIRNAME}/${DAY}/${TIME}
#画像の削除
ptpcam -i
sleep 1.0
ptpcam -i
ptpcam -D
#保存された画像枚数の確認
npic=`find ${DIRNAME}/${DAY}/${TIME} -name "*.DNG" | wc -l`
if [ $cnt -eq $npic ]; then
	#保存先ディレクトリの書き出し
	echo ${DIRNAME}/${DAY}/${TIME}, >> ${DIRNAME}/${DAY}/dirList.txt
else
	#撮影のやり直し
	sudo ./capture.sh ${1}
fi

case "${FLG}" in
	#現像変換を実行
	"CONV11") sudo ./conv.sh ${DIRNAME}/${DAY}/${TIME} 11
	;;
	"CONV12") sudo ./conv.sh ${DIRNAME}/${DAY}/${TIME} 12
	;;
	"CONV21") sudo ./conv.sh ${DIRNAME}/${DAY}/${TIME} 21
	;;
	"CONV22") sudo ./conv.sh ${DIRNAME}/${DAY}/${TIME} 22
	;;
	"CONV31") sudo ./conv.sh ${DIRNAME}/${DAY}/${TIME} 31
	;;
	"CONV32") sudo ./conv.sh ${DIRNAME}/${DAY}/${TIME} 32
	;;
	*) echo done
	;;
esac

