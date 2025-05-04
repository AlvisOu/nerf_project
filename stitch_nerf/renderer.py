#!/usr/bin/env python3

# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

# OUR IMPORTS
import glob
from block_manager import BlockManager
# END OF OUR IMPORTS

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
	parser = argparse.ArgumentParser(description="Run instant neural graphics primitives with additional configuration & output options")
	parser.add_argument("--snapshots", type=str, default="", help="Directory containing snapshots to load.")
	parser.add_argument("--width", "--screenshot_w", type=int, default=0, help="Resolution width of GUI and screenshots.")
	parser.add_argument("--height", "--screenshot_h", type=int, default=0, help="Resolution height of GUI and screenshots.")
	parser.add_argument("--gui", action="store_true", help="Run the testbed GUI interactively.")
	return parser.parse_args()

def get_scene(scene):
	for scenes in [scenes_sdf, scenes_nerf, scenes_image, scenes_volume]:
		if scene in scenes:
			return scenes[scene]
	return None


def teleport_and_look(testbed):
	"""
	Teleport through portal
	"""
	new_matrix = np.copy(testbed.camera_matrix)
	new_matrix[0][3] = dest_x
	new_matrix[2][3] = dest_z
	testbed.set_nerf_camera_matrix(new_matrix)


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
		testbed.init_window(sw, sh)

	# For loading the snapshot
	manager = None
	if args.snapshots:
		snapshot_files = sorted(glob.glob(os.path.join(args.snapshots, "*.msgpack")))
		snapshots = [
			(os.path.splitext(os.path.basename(path))[0], path)
			for path in snapshot_files
		]
		manager = BlockManager(snapshots, "scripts/metadata.sqlite")
		scene_info = get_scene(snapshots[0][1])
		if scene_info is not None:
			snapshots[0] = default_snapshot_filename(scene_info)
		testbed.load_snapshot(snapshots[0][1])

		print(f"Found {len(snapshots)} snapshots:")
		for snap in snapshots:
			print(f" - {snap}")

	# Loop so window stays
	counter = 0
	# curr_snapshot = snapshots[0][1]
	# prev_snapshot = snapshots[1][1]
	# just_entered = False
	print(snapshots)
	while testbed.frame():
		if(counter % 100 == 0):
			print("Camera matrix: ")
			print(testbed.camera_matrix)
			x_pos = testbed.camera_matrix[0][3]
			y_pos = testbed.camera_matrix[1][3]
			z_pos = testbed.camera_matrix[2][3]
			print(f"X: {x_pos:.3f} Y: {y_pos:.3f} Z: {z_pos:.3f}")
			
			result = manager.check_switch(x_pos, y_pos, z_pos, testbed)
			if (result):
				curr_snapshot, new_cam = result
				testbed.load_snapshot(curr_snapshot)
				testbed.set_nerf_camera_matrix(new_cam)

		counter += 1

				# if (result and not just_entered) or (result and result[0] is not prev_snapshot):
				# 	# print("snapshot: " + str(result[0]))


				# 	# temp_snapshot = curr_snapshot #error line
				# 	curr_snapshot, new_cam = result

				# 	testbed.load_snapshot(curr_snapshot)
				# 	# base_cam = testbed.camera_matrix.copy()

				# 	testbed.set_nerf_camera_matrix(new_cam)
				# 	just_entered = True
				# 	prev_snapshot = temp_snapshot
		
				# elif not result: # left portal radius, we can enter again
				# 	print("left the radius")
				# 	just_entered = False

				# if (result and not just_entered):
				# 		print("Result and not just entered")
				# elif (result and result[0] is not prev_snapshot):
				# 	print(result[0] + " is not " + prev_snapshot)

				# if prev_snapshot:	
				# 	print("prev_snapshot: " + str(prev_snapshot))

				

				# if(result[0] is not prev_snapshot):
				# 	print(result[0] + " is not " + prev_snapshot)
				# else:
				# 	print(result[0] + " is " + prev_snapshot)
				
				#what if we only manipulate viewing angle?
				# for row in range(3):
				# 	for col in range(3):
				# 		new_cam[row][col] = base_cam[row][col]

			
				# testbed.camera_matrix = new_cam
				# next_snapshot, dest_x, dest_z = result
				# scene_name = os.path.splitext(os.path.basename(next_snapshot))[0]
				# scene_info = get_scene(scene_name)

				# if scene_info is not None:
				# 	next_snapshot = default_snapshot_filename(scene_info)
				# testbed.load_snapshot(next_snapshot)

				# teleport_and_look(testbed)


