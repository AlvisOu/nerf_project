#!/usr/bin/env python3

# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import argparse
import os
import commentjson as json

import numpy as np

import shutil
import time

from common import *
from scenes import *

from tqdm import tqdm

import pyngp as ngp # noqa

def parse_args():
	# # NEW
	parser = argparse.ArgumentParser(description="Run instant neural graphics primitives with additional configuration & output options")

	parser.add_argument("files", nargs="*", help="Files to be loaded. Can be a scene, network config, snapshot, camera path, or a combination of those.")
	parser.add_argument("--scene", "--training_data", default="", help="The scene to load. Can be the scene's name or a full path to the training data. Can be NeRF dataset, a *.obj/*.stl mesh for training a SDF, an image, or a *.nvdb volume.")
	parser.add_argument("--network", default="", help="Path to the network config. Uses the scene's default if unspecified.")
	parser.add_argument("--load_snapshot", "--snapshot", default="", help="Load this snapshot before training. recommended extension: .ingp/.msgpack")
	parser.add_argument("--nerf_compatibility", action="store_true", help="Matches parameters with original NeRF. Can cause slowness and worse results on some scenes, but helps with high PSNR on synthetic scenes.")
	parser.add_argument("--near_distance", default=-1, type=float, help="Set the distance from the camera at which training rays start for nerf. <0 means use ngp default")
	parser.add_argument("--exposure", default=0.0, type=float, help="Controls the brightness of the image. Positive numbers increase brightness, negative numbers decrease it.")
	parser.add_argument("--save_mesh", default="", help="Output a marching-cubes based mesh from the NeRF or SDF model. Supports OBJ and PLY format.")
	parser.add_argument("--marching_cubes_res", default=256, type=int, help="Sets the resolution for the marching cubes grid.")
	parser.add_argument("--marching_cubes_density_thresh", default=2.5, type=float, help="Sets the density threshold for marching cubes.")

	parser.add_argument("--width", "--screenshot_w", type=int, default=0, help="Resolution width of GUI and screenshots.")
	parser.add_argument("--height", "--screenshot_h", type=int, default=0, help="Resolution height of GUI and screenshots.")

	parser.add_argument("--gui", action="store_true", help="Run the testbed GUI interactively.")
	parser.add_argument("--second_window", action="store_true", help="Open a second window containing a copy of the main output.")
	parser.add_argument("--sharpen", default=0, help="Set amount of sharpening applied to NeRF training images. Range 0.0 to 1.0.")

	return parser.parse_args()

def get_scene(scene):
	for scenes in [scenes_sdf, scenes_nerf, scenes_image, scenes_volume]:
		if scene in scenes:
			return scenes[scene]
	return None

if __name__ == "__main__":
	args = parse_args()
	testbed = ngp.Testbed()

	# For visual display
	if args.gui:
		# Pick a sensible GUI resolution depending on arguments.
		sw = args.width or 1920
		sh = args.height or 1080
		while sw * sh > 1920 * 1080 * 4:
			sw = int(sw / 2)
			sh = int(sh / 2)
		testbed.init_window(sw, sh, second_window=args.second_window)

	# For loading the snapshot
	if args.load_snapshot:
		scene_info = get_scene(args.load_snapshot)
		if scene_info is not None:
			args.load_snapshot = default_snapshot_filename(scene_info)
		testbed.load_snapshot(args.load_snapshot)

	# Loop so window stays
	while testbed.frame():
		continue
	