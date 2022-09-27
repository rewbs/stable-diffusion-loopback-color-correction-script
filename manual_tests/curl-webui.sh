#!/bin/bash
set -o nounset

#!/bin/bash
set -o nounset

function runCurl() {
  CC_TYPE=$1
  CC_WIDTH=$2
  CC_RATE=$3
  CC_DELAY=$4
  CC_INT=$5

  echo '{"fn_index":28,"data":[0,"'$PROMPT'","","None","None","'$(cat $FILE)'",null,null,null,"Draw mask",'$STEPS',"'$DIFF'",4,"fill",'$RESTORE_FACES',false,1,1,7,'$DENOISE','$SEED',-1,0,0,0,false,512,512,"Just resize",false,32,"Inpaint masked","","","Loopback - color correction experiments","Seed","","Steps","",true,false,"<p style=\"margin-bottom:0.75em\">Recommended settings: Sampling Steps: 80-100, Sampler: Euler a, Denoising strength: 0.8</p>",128,8,["left","right","up","down"],1,0.05,"","",1,50,0,false,null,"",'$LOOPS',1,"'$CC_TYPE'",'$CC_WIDTH','$CC_RATE','$CC_DELAY','$CC_INT',false,128,4,"fill",["left","right","up","down"],4,1,"<p style=\"margin-bottom:0.75em\">Will upscale the image to twice the dimensions; use width and height sliders to set tile size</p>",64,"None",null,"",""],"session_hash":"nb79h3wwdee"}' > data.bin

  curl "$HOST" \
    -H 'accept: */*' \
    -H 'content-type: application/json' \
    --data '@./data.bin' \
    --compressed >> out-$(date +%s).bin
}

# function runCurl_origLoopback() {
#
#   echo '{"fn_index":27,"data":[0,"'$PROMPT'","","None","None","'$(cat $FILE)'",null,null,null,"Draw mask",20,"Euler a",4,"fill",'$RESTORE_FACES',false,1,1,7,'$DENOISE','$SEED',-1,0,0,0,false,512,512,"Just resize",false,32,"Inpaint masked","","","Loopback","Seed","","Steps","",true,"<p style=\"margin-bottom:0.75em\">Recommended settings: Sampling Steps: 80-100, Sampler: Euler a, Denoising strength: 0.8</p>",128,4,["left","right","up","down"],1,0.05,"","",1,50,0,false,null,"",false,128,4,"fill",["left","right","up","down"],'$LOOPS',1,"<p style=\"margin-bottom:0.75em\">Will upscale the image to twice the dimensions; use width and height sliders to set tile size</p>",64,"None",null,"",""],"session_hash":"n61d76buoh"}' > data.bin
#
#   curl "$HOST" \
#     -H 'accept: */*' \
#     -H 'content-type: application/json' \
#     --data '@./data.bin' \
#     --compressed >> out-$(date +%s).bin
#
# }

# function setColorCorrection() {
#   echo "WARNING: setting color correction nukes all setting changes"

#   curl "$HOST" \
#   -H 'accept: */*' \
#   -H 'content-type: application/json' \
#   --data-raw '{"fn_index":38,"data":["",true,true,"","","outputs/txt2img-images","outputs/img2img-images","outputs/extras-images","","outputs/txt2img-grids","outputs/img2img-grids","log/images",true,false,"png",false,true,false,"png",false,true,4,100,false,true,false,'$1',true,true,true,"",true,true,true,192,8,["Real-ESRGAN 4x plus","Real-ESRGAN 4x plus anime 6B"],192,8,100,1,1,[],null,true,10,true,8,"CodeFormer",0.5,true,false,false,true,1,24,48,1500,null,true,true,false],"session_hash":"n61d76buoh"}' \
#   --compressed

# }

HOST="https://29300.gradio.app/api/predict/"

DIFF="Euler a"
STEPS=20
RESTORE_FACES=false
SEED=8
LOOPS=80
DENOISE=0.5

function doAll() {
  echo "No color correction"
  runCurl "window" -1 1 0 1000

  echo "Color correct every frame to the input histogram"
  runCurl "input" -1 1 0 1  

  echo "Color correct every frame to average of all frames so far"
  runCurl "window" -1 1 0 1

  echo "Color correct every frame to average of last 5 frames."
  runCurl "window" 5 1 0 1

  echo "Color correct every frame to average of last 10 frames."
  runCurl "window" 10 1 0 1  

  echo "Color correct every frame to average of 5 frames lagging 4 frames behind the current frame."
  runCurl "window" 5 1 4 1

  echo "Color correct every frame to average of 20 frames shifting at 75% the rate of the image generation"
  runCurl "window" 20 0.75 0 1

  echo "Color correct every frame to average of first 75% of frames generated so far."
  runCurl "window" -1 0.75 0 1  

}


# PROMPT="Classy studio photo portrait with (natural skin tones)."
# FILE='hulk.b64'
# DENOISE=0.5
# doAll

PROMPT="Dramatic 4k high detail urban dense utopian cityscape at sunset."
FILE='land.b64'
SEED=20
DENOISE=0.6
doAll

# PROMPT="(Colorful) color photo of a man with yellow hair and a rainbow hat."
# FILE='dali.b64'
# SEED=24
# DENOISE=0.68
# RESTORE_FACES=true
# doAll