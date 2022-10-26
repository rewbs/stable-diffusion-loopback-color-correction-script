# Advanced color correction script forstable-diffusion-webui img2img loopback

## **Update:** Color correction is no longer necessary in most cases, thanks to VAEs. [See here for details](https://www.reddit.com/r/StableDiffusion/comments/ydwnc3/good_news_vae_prevents_the_loopback_magenta_skew/).


[Stable Diffusion](https://stability.ai/blog/stable-diffusion-public-release) is an AI image generation tool. [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) is a web ui for that tool.

This repo provides a script for that web ui that implements an extra img2img loopback mode with advanced color correction options. Specifically, it allows you to color-correct the input to each generated frame to the average histogram of a sliding window of previously generated frames.


## Installation

* Copy `loopback-cc-experiments.py` into the scripts subdirectory in [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui).
* After restarting the webui, you will see a script called `Loopback - color correction experiments` in the scripts list: <img src="https://i.imgur.com/BlsV7nL.jpg" width="640">


## Background

When repeatedly looping a generated image back in as the input image for a subsequent generation, Stable Diffusion skews to magenta.

This recreates in all forks I've tried, as well as in Dream Studio – including on model v1.5. As a result, most UIs now incorporate some form of colour correction to work around the issue, namely by matching the output of every frame to the input's colour range. You can see some examples on https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/847.

Colour-correcting in this way has some drawbacks, such masking desirable colour shifts (e.g. you can't colorise a black and white photo). Therefore, this script is an attempt to provide more control over the color correction logic so that you can tweak it to better suit your usecase.

This is just a workaround: ideally we'd prevent Stable Diffusion's magenta skew, and none of this would be necessary. However, there doesn't appear to be a known root cause for this issue yet, so in the mean time, this script might be useful to some.


## Usage

The script provides the following options:

* **Include input image in target** whether to use the colours of the input image when applying colour correction.
  * `never` - don't use the colours of the input image at all in the colour correction process.
  * `first` - (default) only use the colours of the input image when processing the first frame.
  * `always` - always add  the initial image to the list of images to use for color correction. How much influence the initial image has depends on how many other images are in the color correction window. For example, if you set the window size to `0` and this value to `always`, all frames will be color corrected to the input image (same behaviour as the default with normal loopback mode).
* window size (default: -1) how many frames to average over when computing the target color histogram. -1 means grow the window frames a processed, always starting at frame 0 and ending at the processed frame if slide rate is 1. 
*  **window slide rate** (default: 1) how fast to move the end of the window relative to the frame generation. For example, if the loopback is 80 frames long, a slide rate of `0.5` means that on the last generated frame, the window ends on frame 40.
*  **window lag** (default: 0) how many frames the end of the window should lag behind the current frame. For example, a delay of `5` means the first 5 frames will have no color correction, and from the 6th frame, a window ending at frame 0 will begin to apply. 
*  **color correction interval** (default: 1) do color correction every Nth frame, skip other frames. Default of 1 means color correction is applied on every frame.

### Notes
With this script:

* Color correction is applied **regardless of whether you have color correction enabled in the settings**. The script's sole purpose is to do color correction. If you don't want color correction, use the main loopback script. :)
* Color correction is **always applied after saving the image** for a given loop, but before feeding the image into the next generation step. This is different from "official" color correction logic, where the default behaviour is to save the image after color correction, and you optionally save an extra file before color correction (which typically looks better). See https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/847 for details.


## Examples

All examples below were generated with this script, then converted to video with a color histogram using ffmpeg (see [dir2vid.sh](https://github.com/rewbs/stable-diffusion-loopback-color-correction-script/blob/master/manual_tests/dirs2vid.sh) for specifics). The videos were combined into a grid [following this approach, also with ffmpeg](https://ottverse.com/stack-videos-horizontally-vertically-grid-with-ffmpeg/).


### Natural skin tones from a green init image

* Prompt: `Classy studio photo portrait with (natural skin tones).`
* Params: Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 8-87, Denoising strength: 0.5
* Initial image:
<img src="https://i.imgur.com/eYgtatG.png" width=128>

In the video below:
* **Top-left:** (for reference) No color correction. Here we see the image rapidly skewing to magenta.
* **Top-right:** (for reference) Correct all frames to the input histogram, i.e. default official behaviour. Here we see the generated images cannot pull away from the green palette of the input.
* **Mid-left:** Correct to the average of input plus all previously generated frames (window size: -1; slide rate: 1; lag: 0). Here we see natural skin tones emerging.
* **Mid-right:** Correct to average of a window 10 frames wide, moving at 75% the speed of generation (window size: 10; slide rate: 0.75; lag: 0). This is roughly equivalent to the previous.
* **Bot-left:** Correct to the average of a window 5 frames wide, running up to the last generated frame (window size: 5; slide rate: 1; lag: 0). Here we see a blue skew emerging towards the end of the loop, which is common with narrow windows that only account for the most recently generated images. The cause is not known but is possibly a cyan skew related to overcorrecting away from the magenta skew.
* **Bot-right:** Correct to the average of a window 5 frames wide, lagging 4 frames behind the last generated frame (window size: 5; slide rate: 1; lag: 4). This helps mitigate the cyan/blue skew, resulting in simlar results to the middle row.

https://user-images.githubusercontent.com/74455/192528827-c4696a99-9cf6-4ff7-8771-78ef835e7d0c.mp4


### Colour from a black and white init image

* Prompt: `(Colorful) color photo of a man with yellow hair and a rainbow hat.`
* Params: Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 24-103, Denoising strength: 0.68
* Initial image:
<img src="https://i.imgur.com/1d6ib3F.png" width=128>

In the video below:
* **Top-left:** (for reference) No color correction. Here the image does not skew to magenta too quickly because the denoise strength is a bit higher. However, the image still degrades aggressively.
* **Top-right:** (for reference) Correct all frames to the input histogram, i.e. default official behaviour. Here we see the generated images struggle to introduce colour: each generation adds a bit of colour, but is reset to B&W before being fed back into the loop, resulting in a washed out result overall.
* **Mid-left:** Correct to the average of input plus all previously generated frames (window size: -1; slide rate: 1; lag: 0). Here we get pretty good results but still a little washed out.
* **Mid-right:** Correct to average of the first 75% of images generated so far (window size: -1; slide rate: 0.75; lag: 0). It's interesting to see how a little change in color palette can lead to completely different output images from about frame 15.
* **Bot-left:** Correct to the average of a window 5 frames wide, running up to the last generated frame (window size: 5; slide rate: 1; lag: 0).
* **Bot-right:** Correct to the average of a window 5 frames wide, lagging 4 frames behind the last generated frame (window size: 5; slide rate: 1; lag: 4). 

https://user-images.githubusercontent.com/74455/192535122-dbb1d5b4-3338-4410-bdc4-eee7e33818f5.mp4

### Counter example

In this example, the "official" color correction is clearly the winner. The input color palette is perfectly fine for the type of output being generated. Any attempt to apply a different correction seems to result in a reduction of the colours used, and ultimately a simplification and/or undesirable color fade. I don't know why this is: the alternative color corrections should theoretically allow the animation to veer into different colors, without necessarily converging into murkiness. :)

* Prompt: Dramatic 4k high detail urban dense utopian cityscape at sunset.
* Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 20-99, Size: 512x512, Denoising strength: 0.6
* Initial image:
<img src="https://i.imgur.com/oCniFsz.png" width=128>

https://user-images.githubusercontent.com/74455/192546570-6ea0c224-daea-46e8-b578-7fee30f6808d.mp4
