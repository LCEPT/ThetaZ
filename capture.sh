#!/bin/bash

#保存先の親ディレクトリをコマンドライン引数（1番目）から取得
DIRNAME=${1}

#撮影後の動作をコマンドライン引数（2番目）から取得
FLG=${2}

#保存先ディレクトリの作成
DAY=`date '+%y%m%d'`
TIME=`date '+%H%M%S'`
mkdir -p ${DIRNAME}/${DAY}
chmod 777 ${DIRNAME}/${DAY}
mkdir ${DIRNAME}/${DAY}/${TIME}
chmod 777 ${DIRNAME}/${DAY}/${TIME}

# ── ここからログ設定 ──
# ログファイルパス
LOGFILE="${DIRNAME}/${DAY}/${TIME}/capture.log"

# 以降のすべての出力を tee でログに追記
exec > >(tee -a "$LOGFILE") 2>&1
# ── ここまでログ設定 ──

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


# 指定ディレクトリ内に "*EVlist.csv" があれば最初の１つを使い、なければ従来のファイル名にフォールバック
CSV_PATTERN="${DIRNAME}"/*EVlist.csv
if compgen -G "${CSV_PATTERN}" > /dev/null; then
    EVLIST_FILE=$(ls "${CSV_PATTERN}" | head -n1)
else
    EVLIST_FILE="${DIRNAME}/EVlist.csv"
fi

echo ">> Using EV list file: ${EVLIST_FILE}"

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
done < "${EVLIST_FILE}"
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

# Exif 情報を参照して picInfo.csv を生成
#    (DNGファイル名, TIFFファイル名, ISO, ExposureTimeを昇順で出力)
picinfo_tmp="${DIRNAME}/${DAY}/${TIME}/picInfo.csv"
if command -v exiftool >/dev/null 2>&1; then
    # ヘッダ行を出力
    # DNGファイルを昇順にループ
    for f in $(ls "${DIRNAME}/${DAY}/${TIME}"/*.DNG | sort); do
        base=$(basename "$f" .DNG)
		# Exif 情報を取得
        iso=$(exiftool -ISO -s3 "$f")
        exp=$(exiftool -ExposureTime -s3 "$f")
        fnum=$(exiftool -FNumber -s3 "$f")
        # CSV に書き出し
        echo "${base}.DNG,${base}.tiff,${iso},${exp},${fnum}" >> "${picinfo_tmp}"
    done
    echo "Generated picInfo.csv"
else
    echo "Error: exiftool not installed. picInfo.csv not generated." >&2
    exit 1
fi

# --- EVlist.csv と照合してミスマッチがあれば再撮影 ---
mismatch=false
# EVlist.csv の 1列目=imageNo, 2=ISO, 3=ExposureTime
while IFS=, read -r imgno iso_exp exp_exp _; do
    # 新規 CSV から該当行を取得
    line=$(grep "^${imgno}\.DNG," "${picinfo_tmp}")
    [ -z "$line" ] && { mismatch=true; break; }
    iso_act=$(echo "$line" | cut -d, -f3)
    exp_act=$(echo "$line" | cut -d, -f4)
    if [ "$iso_exp" != "$iso_act" ] || [ "$exp_exp" != "$exp_act" ]; then
        echo ">> Mismatch for ${imgno}: expected ISO=${iso_exp},Exp=${exp_exp} but got ISO=${iso_act},Exp=${exp_act}"
        mismatch=true
        break
    fi
done < "${EVLIST_FILE}"

if $mismatch; then
    echo ">> Detected mismatch, retrying capture..."
    sudo bash "$0" "${DIRNAME}" "${FLG}"
    exit 1
else
    # 問題なければ保存先ディレクトリの書き出し
    echo ${DIRNAME}/${DAY}/${TIME}, >> ${DIRNAME}/${DAY}/dirList.txt
    echo ">> Captured successfully."
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

