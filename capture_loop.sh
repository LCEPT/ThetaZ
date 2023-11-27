#!/bin/bash

#撮影日時リストをコマンドライン引数から取得
FNAME=${1}
#保存先の親ディレクトリをコマンドライン引数から取得
DIRNAME=`dirname ${1}`

#撮影予定日時に撮影を実行
while read -r line
do
	echo "Next shooting time:" ${line}
	cmp=`date --date="$line" +%s`
	now=`date +%s`
	#撮影日時リストに現時刻よりも過去の時刻がある場合はskip
	if [ "$now" -gt "$cmp" ]; then
		echo "skip"
	#撮影予定時刻になるまでカウントダウン
	else
		while [ "$now" -lt "$cmp" ]
		do
			diff=$((cmp - now))
			let day="$diff / 86400"
			let diff="$diff % 86400"
			let hour="$diff / 3600"
			let diff="$diff % 3600"
			let minute="$diff / 60"
			let second="$diff % 60"
    		message="Next shooting will start in "
			printf '\r%s %02dDay %02d:%02d:%02d' "${message}" "${day}" "${hour}" "${minute}" "${second}" 
    		sleep 1
    		now=`date +%s`
    	done
		echo "shoot"
		sudo ./capture.sh ${DIRNAME}
	fi
done < ${FNAME}


