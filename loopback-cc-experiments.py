import numpy as np
import logging
from pprint import pformat
from tqdm import trange
import glob
import cv2

import modules.scripts as scripts
import gradio as gr

from modules import processing, shared, sd_samplers, images
from modules.processing import Processed
from modules.sd_samplers import samplers
from modules.shared import opts, cmd_opts, state

class Script(scripts.Script):
    def title(self):
        return "Loopback - color correction experiments"

    def show(self, is_img2img):
        return is_img2img

    def ui(self, is_img2img):
        loops = gr.Slider(minimum=1, maximum=500, step=1, label='Loops', value=4)
        denoising_strength_change_factor = gr.Slider(minimum=0.9, maximum=1.1, step=0.01, label='Denoising strength change factor', value=1)
        cc_target_type = gr.Radio(label='Color correction target', choices=['window', 'input'], value='window')
        cc_window_size = gr.Slider(minimum=-1, maximum=50, step=1, label='Color correction window width', value=-1)
        cc_window_rate = gr.Slider(minimum=0.1, maximum=1, step=0.1, label='Color correction window slide rate', value=1)
        cc_window_delay = gr.Slider(minimum=1, maximum=10, step=1, label='Color correction delay', value=0)
        cc_interval = gr.Slider(minimum=1, maximum=50, step=1, label='Color correction interval', value=1)

        return [loops, denoising_strength_change_factor, cc_target_type, cc_window_size, cc_window_rate, cc_window_delay, cc_interval]

    def run(self, p, loops, denoising_strength_change_factor, cc_target_type, cc_window_size, cc_window_rate, cc_window_delay, cc_interval):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

        processing.fix_seed(p)
        batch_count = p.n_iter

        logging.info(f"Starting loopback with: \n"
        f"loops: {loops}; \n"
        f"initial seed: {p.seed}; \n"        
        f"initial denoising strength: {p.denoising_strength}; \n"
        f"denoising strength change factor: {denoising_strength_change_factor}; \n"
        f"color correction enabled in main options?: {opts.img2img_color_correction}; \n"
        f"Color correction window size: {cc_window_size} \n"
        f"Color correction window slide rate: {cc_window_rate} \n"
        f"Color correction window start delay: {cc_window_delay} \n"
        f"apply cc every N loops: {cc_interval} \n")

        p.batch_size = 1
        p.n_iter = 1

        output_images, info = None, None
        initial_seed = None
        initial_info = None

        grids = []
        all_images = []
        state.job_count = loops * batch_count

        # HACK - ideally scripts could opt in to hooks at various points in the processing loop including file saving.
        logging.info("Overriding color correction option to false in main processing so that we can control color correction in the script loop.")
        old_cc_opt = opts.img2img_color_correction
        opts.img2img_color_correction = False
        p.color_corrections = None

        input_histogram = processing.setup_color_correction(p.init_images[0])

        try:

            for n in range(batch_count):
                history = []

                for i in range(loops):
                    p.n_iter = 1
                    p.batch_size = 1
                    p.do_not_save_grid = True

                    loop_index = i+1
                    cc_window_start, cc_window_end  = self.compute_cc_target_window(loop_index, cc_window_delay, cc_window_size, cc_window_rate)
                    do_cc = loop_index%cc_interval==0

                    p.extra_generation_params = {
                        "Batch": n,
                        "Loop:": loop_index,
                        "Denoising strength change factor": denoising_strength_change_factor,
                        "Color correction interval": cc_interval,
                        "Color correction target type": cc_target_type,
                        "Color correction window size": cc_window_size,
                        "Color correction window slide rate": cc_window_rate,
                        "Color correction on this image": do_cc,
                        "Color correction window start on this image": cc_window_start,
                        "Color correction window end on this image": cc_window_end
                    }
                    
                    state.job = f"Iteration {loop_index}/{loops}, batch {n + 1}/{batch_count}"
                    logging.info(f"it:{loop_index} - seed:{p.seed}; denoising_strength:{p.denoising_strength}; ")
                    logging.info(pformat(p.extra_generation_params))
                    logging.debug(pformat(p))

                    processed = processing.process_images(p)

                    if initial_seed is None:
                        initial_seed = processed.seed
                        initial_info = processed.info

                    init_img = processed.images[0]

                    if cc_target_type == 'window':
                        all_images = history.copy()
                        all_images.append(processed.images[0])
                        target_histogram = self.compute_cc_target(all_images, cc_window_start, cc_window_end)
                    else:
                        target_histogram = input_histogram

                    if do_cc:
                        if target_histogram is None:
                            logging.info(f"Skipping color correction on loop {loop_index} (cc interval: {cc_interval}, target frames: {cc_window_start} to {cc_window_end})")                            
                        else:
                            if cc_target_type == 'window':
                                logging.info(f"Applying color correction on loop {loop_index} (cc interval: {cc_interval}, target frames: {cc_window_start} to {cc_window_end})")
                            else:
                                logging.info(f"Applying color correction on loop {loop_index} (cc interval: {cc_interval}, using input image)")
                            init_img = processing.apply_color_correction(target_histogram, init_img)
                            #images.save_image(init_img, p.outpath_samples, "", p.seed, p.prompt, opts.samples_format, info=None, p=p, suffix="-after-color-correction")
                    else:
                        logging.debug(f"Skipping color correction on loop {loop_index} because interval condition not met (interval: {cc_interval}), target frames: {cc_window_start} to {cc_window_end})")

                    p.init_images = [init_img]
                    p.seed = processed.seed + 1
                    p.denoising_strength = min(max(p.denoising_strength * denoising_strength_change_factor, 0.1), 1)
                    history.append(processed.images[0])

                grid = images.image_grid(history, rows=1)
                if opts.grid_save:
                    images.save_image(grid, p.outpath_grids, "grid", initial_seed, p.prompt, opts.grid_format, info=info, short_filename=not opts.grid_extended_filename, grid=True, p=p)

                grids.append(grid)
                all_images += history

            if opts.return_grid:
                all_images = grids + all_images

            processed = Processed(p, all_images, initial_seed, initial_info)
            return processed

        finally:
            logging.info("Restoring CC option to: %s", old_cc_opt)
            opts.img2img_color_correction = old_cc_opt
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)

    def compute_cc_target_window(self, current_pos, window_delay, window_size, window_rate):
        cc_window_end = round((current_pos-window_delay)*window_rate)
        if window_size == -1:
            cc_window_start = 0
        else:
            cc_window_start = max(0, cc_window_end-window_size)
        return cc_window_start, cc_window_end


    def compute_cc_target(self, all_images, cc_window_start, cc_window_end):
        target_histogram = None
        
        if (cc_window_start<cc_window_end and cc_window_start>=0):
            target_images = all_images[cc_window_start:cc_window_end]
            logging.debug(f"target_images length: {len(target_images)}")
            
            target_histogram = (cv2.cvtColor(np.asarray(target_images[0].copy()), cv2.COLOR_RGB2LAB)*0).astype('float64')
            for img in target_images:
                target_histogram_component = cv2.cvtColor(np.asarray(img.copy()), cv2.COLOR_RGB2LAB).astype('float64')
                target_histogram += (target_histogram_component/len(target_images)).astype('float64')
                        
            target_histogram=target_histogram.astype('uint8')
        
        return target_histogram