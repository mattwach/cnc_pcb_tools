"""Gcode checker library"""

import atexit
import argparse
import math
import os
import pathlib
import sys
from typing import List, Optional
import __main__

#pylint:disable=global-statement
#pylint:disable=invalid-name
#pylint:disable=missing-function-docstring

def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description='Load and check a GCode file.')
  parser.add_argument('filename', type=str,
                      help='GCode filename')
  return parser.parse_args()

class Error(Exception):
  pass

class BadTokenError(Error):
  pass

class MissingKeyError(Error):
  pass

class NotAllPassingError(Error):
  pass

class TemplatePathNotFoundError(Error):
  pass

class TooManyTokensError(Error):
  pass

class UnknownGCodeError(Error):
  pass

class UnexpectedUnitsError(Error):
  pass

class UnknownParameterError(Error):
  pass

all_passing = True

def check_all_passing():
  if not all_passing:
    print()
    raise NotAllPassingError('Some tests failed. (see above)')

atexit.register(check_all_passing)


class GCode:
  """Holds parsed information about a GCode line."""
  def __init__(self):
    self.code = None
    self.x = 0.0
    self.y = 0.0
    self.z = 0.0
    self.feed = 0.0
    self.rpm = 0.0
    self.line_number = 0
    self.units = ''
    self.is_rapid = False

    self.x_delta = 0
    self.y_delta = 0
    self.z_delta = 0
    self.feed_delta = 0
    self.rpm_delta = 0

  def copy(self):
    c = GCode()
    c.x = self.x
    c.y = self.y
    c.z = self.z
    c.feed = self.feed
    c.rpm = self.rpm
    c.units = self.units
    return c


class GCodeChecker:
  """GCodeChecker is the object a user instantiates to load the gcode file and check it."""
  def __init__(self):
    args = parse_args()
    self.codes = load_gcode(args.filename)
    self.dir = pathlib.Path(args.filename).absolute().parents[0]

  def dump_properties(self):
    print('Properties:')
    print(f'  lines: {self.codes[-1].line_number}')
    print(f'  codes: {len(self.codes)}')
    print(f'  units: {self.units()}')
    print(f'  xrange: {self.min_x()} .. {self.max_x()}')
    print(f'  yrange: {self.min_y()} .. {self.max_y()}')
    print(f'  zrange: {self.min_z()} .. {self.max_z()}')
    print(f'  max_plunge_feed_z: {self.max_plunge_feed_z()}')
    print(f'  max_cut_feed_xy: {self.max_cut_feed_xy()}')

    print()

  def aggregate(self, getter, combiner):
    values = [getter(code) for code in self.codes]
    return combiner(values)

  def min_x(self):
    return self.aggregate(lambda code: code.x, min)

  def max_x(self):
    return self.aggregate(lambda code: code.x, max)

  def min_y(self):
    return self.aggregate(lambda code: code.y, min)

  def max_y(self):
    return self.aggregate(lambda code: code.y, max)

  def min_z(self):
    return self.aggregate(lambda code: code.z, min)

  def max_z(self):
    return self.aggregate(lambda code: code.z, max)

  def max_rpm(self):
    return self.aggregate(lambda code: code.rpm, max)

  def max_z_plunge(self):
    def check(code):
      if code.z >= 0.0:
        return 0.0
      if code.z_delta >= 0.0:
        return 0.0
      if code.z - code.z_delta > 0:
        return -code.z
      return -code.z_delta
    return self.aggregate(check, max)

  def max_plunge_feed_z(self):
    def check_z(code):
      if code.rpm == 0.0:
        return 0.0
      if code.z_delta >= 0.0:
        return 0.0
      return code.feed
    return self.aggregate(check_z, max)

  def max_cut_feed_xy(self):
    def check(code):
      if code.z >= 0.0:
        return 0.0
      if code.x_delta == 0.0 and code.y_delta == 0.0:
        return 0.0
      return code.feed
    return self.aggregate(check, max)

  def has_code(self, code):
    if len(code) == 2:
      code = code[0] + '0' + code[1]
    for c in self.codes:
      if c.code == code:
        return True
    return False

  def units(self):
    return set((code.units for code in self.codes))

  # Assertions
  def assert_true(self, msg: str, cond: bool) -> None:
    if cond:
      print(f'{msg}: OK')
    else:
      print(f'{msg}: FAIL')
      global all_passing
      all_passing = False

  def assert_false(self, msg: str, cond: bool) -> None:
    self.assert_true(msg, not cond)

  def assert_spinning(self):
    spin_ok = True
    for code in self.codes:
      if code.z < 0.0 and code.rpm == 0.0:
        spin_ok = False
    self.assert_true('Spinning in material', spin_ok)

  def assert_gt(self, msg, val, ref):
    msg = f'{msg}: {val} > {ref}'
    self.assert_true(msg, val > ref)

  def assert_lt(self, msg, val, ref):
    msg = f'{msg}: {val} < {ref}'
    self.assert_true(msg, val < ref)

  def assert_gte(self, msg, val, ref):
    msg = f'{msg}: {val} >= {ref}'
    self.assert_true(msg, val >= ref)

  def assert_lte(self, msg, val, ref):
    msg = f'{msg}: {val} <= {ref}'
    self.assert_true(msg, val <= ref)

  # Test file creation

  def create_test_gcode(
      self,
      template_filename: str,
      output_filename: str,
      padding: float) -> None:
    if not all_passing:
      print('Skipping test gcode output (tests are failing)')
    if self.units() != set(['MM']):
      raise UnexpectedUnitsError('Only MM units are supported for test files.')
    template_path = pathlib.Path(template_filename)
    if not template_path.exists():
      template_path = pathlib.Path(
          os.path.join(os.path.dirname(__main__.__file__), template_path))

    if not template_path.exists():
      raise TemplatePathNotFoundError(
          'Did not find template path: %s' % template_path)

    x_start = math.floor(self.min_x() - padding)
    x_end = math.ceil(self.max_x() + padding)
    y_start = math.ceil(self.max_y() + padding)
    y_end = math.floor(self.min_y() - padding)

    template_data = {
        'spindle_speed': self.max_rpm(),
        'unit_code': 21,
        'units': 'MM',
        'x_end': x_end,
        'x_start': x_start,
        'xy_feedrate': self.max_cut_feed_xy(),
        'y_end': y_end,
        'y_start': y_start,
        'z_dwell_feedrate': 200,
        'z_initial_height': 10,
        'z_plunge_feedrate': 60,
    }

    template = template_path.read_text(encoding='utf8')
    try:
      output = template.format(**template_data)
    except KeyError as e:
      raise MissingKeyError('Missing template key: %s' % e) from e

    output_path = self.dir / output_filename
    with open(output_path, 'w', encoding='utf8') as fout:
      fout.write(output)

    print('Wrote %s' % output_path)


def load_gcode(filename: str) -> List[str]:
  lines = []
  with open(filename, 'r', encoding='utf8') as fin:
    previous_code = None
    for line_number0, line in enumerate(fin):
      line_number = line_number0 + 1
      try:
        code = process_line(previous_code, line, line_number)
      except Error as e:
        sys.stderr.write(f'Line {line_number}\n')
        sys.stderr.write(f'{line}')
        sys.stderr.write(f'{e}\n')
        sys.exit(1)
      if code:
        lines.append(code)
        previous_code = code
  return lines


def process_line(
    previous_code: GCode, line: str, line_number: int) -> Optional[GCode]:
  line = line.strip().upper().split('(')[0]
  if not line:
    return None
  if previous_code:
    code = previous_code.copy()
  else:
    code = GCode()
  code.line_number = line_number
  tokens = make_tokens(line)
  code.code = tokens[0]
  if code.code not in CODES:
    raise UnknownGCodeError('Unknown GCode')
  CODES[code.code](code, tokens)
  return code

def make_tokens(line: str) -> List[str]:
  tokens = []
  t = []
  for c in line.strip().upper():
    if c == ';':
      #start of a comment
      break
    if t:
      if c in '-0123456789.':
        t.append(c)
        continue

      tokens.append(''.join(t))
      t = []

      if c in ' \t':
        continue

    if not t:
      if c in ' \t':
        continue
      if 'A' <= c <= 'Z':
        t = [c]
      else:
        raise BadTokenError('Bad token')

  if t:
    tokens.append(''.join(t))

  if tokens:
    if len(tokens[0]) == 2:
      # G1 -> G01
      tokens[0] = f'{tokens[0][0]}0{tokens[0][1]}'

  return tokens

#
# GCODE handlers below this point
#

def linear_move(code: GCode, tokens: List[str]):
  for t in tokens[1:]:
    parm = t[0]
    val = float(t[1:])
    if parm == 'F':
      code.feed_delta = val - code.feed
      code.feed = val
    elif parm == 'X':
      code.x_delta = val - code.x
      code.x = val
    elif parm == 'Y':
      code.y_delta = val - code.y
      code.y = val
    elif parm == 'Z':
      code.z_delta = val - code.z
      code.z = val
    else:
      raise UnknownParameterError(f'Unknown parameter: {parm}')

def ignore(unused_code: GCode, unused_tokens: List[str]):
  pass

def rapid_move(code: GCode, tokens: List[str]):
  code.is_rapid = True
  linear_move(code, tokens)

def set_units_to_mm(code: GCode, tokens: List[str]):
  if len(tokens) > 1:
    raise TooManyTokensError('Too many tokens')
  code.units = 'MM'

def start_spindle(code: GCode, tokens: List[str]):
  for t in tokens[1:]:
    parm = t[0]
    val = float(t[1:])
    if parm == 'S':
      code.rpm_delta = val - code.rpm
      code.rpm = val
    else:
      raise UnknownParameterError(f'Unknown parameter: {parm}')

def stop_spindle(code: GCode, tokens: List[str]):
  if len(tokens) > 1:
    raise TooManyTokensError('Too many tokens')
  code.rpm = 0


CODES = {
    'G00': rapid_move,
    'G01': linear_move,
    'G17': ignore,  # set plane to XY (assumed to be true)
    'G21': set_units_to_mm,
    'G90': ignore,  # absolute positioning
    'G94': ignore,  # feed per minute
    'M00': ignore,  # unconditional stop
    'M03': start_spindle,
    'M05': stop_spindle,
    'T01': ignore,  # change to tool 1
}
