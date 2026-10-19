#!/bin/bash
# render-chunks.sh page out-prefix total-frames [chunk]: renders 16:9 in finished pieces, skipping pieces already done
cd /home/user/Video-Genx2; P=$1; OUT=$2; N=$3; C=${4:-300}
for ((a=0; a<N; a+=C)); do b=$((a+C)); f=$OUT-chunk-$(printf %05d $a).mp4
  if ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" >/dev/null 2>&1; then continue; fi
  node scripts/render-video.js --page $P --width 1920 --height 1080 --query aspect=16x9 --from $a --to $b --out $f.tmp.mp4 >/dev/null 2>&1 && mv $f.tmp.mp4 $f && echo "chunk $a done"
done
ls $OUT-chunk-*.mp4 | sed 's/.*\//file /' > $OUT-chunks.txt
ffmpeg -y -v error -f concat -safe 0 -i $OUT-chunks.txt -c copy -movflags +faststart $OUT-silent.mp4 && echo "joined $OUT-silent.mp4"
