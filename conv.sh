#!/bin/bash

#カレントディレクトリを取得
CDIR=`pwd`

# 入力パラメータ
DIRNAME=$1   # RAW画像(.DNG) が格納されたディレクトリ
FLG=$2       # オプションフラグ（11, 12, 21, ... など）

#作業デレクトリを画像保存先に変更
cd "$DIRNAME" || { echo "Cannot cd to $DIRNAME"; exit 1; }
#sysInfo.csvを検索
SYSFNAME=$(ls | grep "sysInfo" | head -n1)

# 1) Exif 情報を参照して picInfo.csv を生成
#    (FileName, ISO, ExposureTime, FNumber をファイル名で昇順ソート)
if command -v exiftool >/dev/null 2>&1; then
    # 既存のpicInfo.csvを空にする（上書き用）
    : > picInfo.csv
    # DNGファイルを昇順にループ
    for f in $(ls *.DNG | sort); do
        # Exif 情報を取得
        iso=$(exiftool -ISO -s3 "$f")
        exp=$(exiftool -ExposureTime -s3 "$f")
        fnum=$(exiftool -FNumber -s3 "$f")
        # 対応する TIFF ファイル名（拡張子を .tiff に変更）
        tiff="${f%.*}.tiff"
        # CSV に書き出し
        echo "${f},${tiff},${iso},${exp},${fnum}" >> picInfo.csv
    done
    echo "Updating picInfo.csv in $DIRNAME"
else
    echo "Warning: exiftool not installed. picInfo.csv not updated." >&2
fi

# 2) dcraw 用のガンマ設定引数を選択
case "$FLG" in
    11) GAMMA_ARGS=( -g 1 1 ) ;;
    12) GAMMA_ARGS=( -g 2.4 12.92 ) ;;
    21) GAMMA_ARGS=( -g 1 1 ) ;;
    22) GAMMA_ARGS=( -g 2.4 12.92 ) ;;
    31) GAMMA_ARGS=( -g 1 1 ) ;;
    32) GAMMA_ARGS=( -g 2.4 12.92 ) ;;
    *)  GAMMA_ARGS=( -g 1 1 ) ;;  # デフォルト
esac

# 3) RAW → TIFF 変換（ファイルをワイルドカードではなくループで処理）
echo "Converting DNG to TIFF with dcraw ${GAMMA_ARGS[*]}"
shopt -s nullglob
DNG_FILES=( *.DNG )
if [ ${#DNG_FILES[@]} -eq 0 ]; then
    echo "No .DNG files found in $DIRNAME" >&2
else
    for f in "${DNG_FILES[@]}"; do
        echo "Processing $f..."
        dcraw -v -T "${GAMMA_ARGS[@]}" -W "$f"
    done
    echo "Raw to TIFF conversion done."
fi


#作業デレクトリをもとに戻す
cd ${CDIR}

#pythonスクリプトでXYZ変換
case "$FLG" in
	"11") echo gamma 1.0 output XYZ data
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -o 1 -g 1 -s ${SYSFNAME}
		;;
	"12") echo gamma 2.4 output XYZ data
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -o 1 -g 2 -s ${SYSFNAME}
		;;
	"21") echo gamma 1.0 output Y data
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -o 2 -g 1 -s ${SYSFNAME}
		;;
	"22") echo gamma 2.4 output XYZ data 
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -o 2 -g 2 -s ${SYSFNAME}
		;;
	"31") echo gamma 1.0 output RGB data
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -o 3 -g 1 -s ${SYSFNAME}
		;;
	"32") echo gamma 2.4 output RGB data 
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -o 3 -g 2 -s ${SYSFNAME}
		;;
	*)   echo gamma 1.0 output XYZ data
		python3 conv_hdr_xyz.py -i ${DIRNAME}/${dir_data} -s ${SYSFNAME}
		;;
esac
