#!/bin/bash

for d in */ ; do
    EXP_NAME=${d%?}
    echo "Converting $EXP_NAME..."
    ffmpeg -framerate 10 -pattern_type glob -i $EXP_NAME/'*.png' -vf "drawtext=fontfile=Verdana.ttf: text='$EXP_NAME; frame %{frame_num}': start_number=1: x=w-tw*1.1: y=h-lh*1.5: fontcolor=blue: fontsize=20: box=1: boxcolor=white@0.4: boxborderw=5"  -c:v libx264 -pix_fmt yuv420p  ./$EXP_NAME.mp4
    ffmpeg -framerate 10 -pattern_type glob -i $EXP_NAME/'*.png' -filter_complex "histogram=display_mode=overlay,scale=512:512" -an -c:v libx264 -pix_fmt yuv420p ./$EXP_NAME-histo.mp4
    ffmpeg -i ./$EXP_NAME.mp4 -i ./$EXP_NAME-histo.mp4 -filter_complex hstack ./$EXP_NAME-combined.mp4
done