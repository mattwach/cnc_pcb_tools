#!/usr/bin/env python3
"""Checks a drill gcode file."""

import check_gcode
import check_pcb_common

check = check_gcode.GCodeChecker()
# checks that are common for all files (board dimensions, assert spinning, etc)
check_pcb_common.check_common(check)
check.assert_gt('min_z', check.min_z(), -1.8)
check.assert_lt('max_z_plunge', check.max_z_plunge(), 1.8)
# don't move the drill in the XY direction while cutting
check.assert_lte('max_cut_feed_xy', check.max_cut_feed_xy(), 0.0)
