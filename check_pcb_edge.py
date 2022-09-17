#!/usr/bin/env python3
"""Checks a edge gcode file.

You should edit this file as needed to conform to your particular machine and process.
"""

import check_gcode
import check_pcb_common

check = check_gcode.GCodeChecker()
# checks that are common for all files (board dimensions, assert spinning, etc)
check_pcb_common.check_common(check)
check.assert_gt('min_z', check.min_z(), -1.8)
check.assert_lte('max_z_plunge', check.max_z_plunge(), 0.61)
check.assert_lte('max_cut_feed_xy', check.max_cut_feed_xy(), 120.0)

# the -1.0 padding account for an assumed 2.0 (or more) thick edge cut
check.create_test_gcode('test_template.txt', 'test.nc', -1.0)
