#!/bin/zsh

function move() {
    NUM=$1
    DEST=$2
    mkdir $DEST
    mv -- *(D.[1,$NUM]) $DEST
}

move 160 no-cc
move 160 cc-to-input
move 160 cc-to-average
move 160 cc-5-last-frames
move 160 cc-5-last-frames-lag-1
move 160 cc-5-last-frames-lag-4
move 160 cc-10-frames-75pc-behind
move 160 cc-first-75pc-frames