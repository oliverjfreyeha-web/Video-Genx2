#!/usr/bin/env bash
# Mix audio/voiceover.wav (voice chain: high-pass, de-mud, presence lift, de-ess, gentle compression) (raised to about -16 LUFS; loudnorm is avoided because its look-ahead truncates the tail) over audio/music.wav (music ducks under the voice) and mux onto the rendered video.
#   scripts/mix-audio.sh [video-in] [video-out]
set -euo pipefail
cd "$(dirname "$0")/.."
IN=${1:-renders/google-ads-explainer-1080p-silent.mp4}
OUT=${2:-renders/google-ads-explainer-1080p.mp4}
VO=${VO:-audio/voiceover.wav}        # override: VO=audio/other-vo.wav MUSIC=audio/other-music.wav scripts/mix-audio.sh in.mp4 out.mp4
MUSIC=${MUSIC:-audio/music.wav}

ffmpeg -y -loglevel error -i "$IN" -i "$VO" -i "$MUSIC" -filter_complex "
  [1:a]aformat=sample_rates=44100:channel_layouts=stereo,highpass=f=90,equalizer=f=250:width_type=o:width=1.2:g=-2,equalizer=f=3500:width_type=o:width=1.4:g=2.5,deesser=i=0.35,acompressor=threshold=0.12:ratio=2.5:attack=8:release=120:makeup=1.6,volume=3.2dB,asplit=2[vo][key];
  [2:a]highpass=f=35,equalizer=f=2200:width_type=o:width=1.6:g=-3,volume=-12dB[bed];
  [bed][key]sidechaincompress=threshold=0.02:ratio=5:attack=40:release=450:makeup=1[ducked];
  [vo][ducked]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.89:level=false[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
echo "wrote $OUT"
