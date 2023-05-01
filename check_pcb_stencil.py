#!/usr/bin/env python3
"""Checks a copper isolation gcode file."""

import check_gcode
import check_pcb_common

check = check_gcode.GCodeChecker()
# checks that are common for all files (board dimensions, assert spinning, etc)
check_pcb_common.check_common(check, maxx=200.0, miny=-120.0)
check.assert_gt('min_z', check.min_z(), -0.21)
check.assert_lte('max_z_plunge', check.max_z_plunge(), 0.2)
check.assert_lte('max_plunge_feed_z', check.max_plunge_feed_z(), 101.0)
check.assert_lte('max_cut_feed_xy', check.max_cut_feed_xy(), 300.0)
