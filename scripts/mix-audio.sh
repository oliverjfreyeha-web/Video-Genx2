#!/usr/bin/env bash
# Mix audio/voiceover.wav over audio/music.wav (music ducks under the voice) and mux onto the rendered video.
#   scripts/mix-audio.sh [video-in] [video-out]
set -euo pipefail
cd "$(dirname "$0")/.."
IN=${1:-renders/google-ads-explainer-1080p.mp4}
OUT=${2:-renders/google-ads-explainer-1080p-voiced.mp4}

ffmpeg -y -loglevel error -i "$IN" -i audio/voiceover.wav -i audio/music.wav -filter_complex "
  [1:a]aformat=sample_rates=44100:channel_layouts=stereo,highpass=f=80,loudnorm=I=-16:TP=-2:LRA=7,asplit=2[vo][key];
  [2:a]highpass=f=35,equalizer=f=2200:width_type=o:width=1.6:g=-3,volume=-12dB[bed];
  [bed][key]sidechaincompress=threshold=0.02:ratio=5:attack=40:release=450:makeup=1[ducked];
  [vo][ducked]amix=inputs=2:normalize=0,alimiter=limit=0.89:level=false[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
echo "wrote $OUT"
