#!/usr/bin/env python3

"""Adjusts a Candle CNC heightmap by the requested offset.

Example usage:
  python3 candle_heightmap_adjust --input height.map --offset 0.1
"""

from typing import List

import argparse
import pathlib
import sys

class Error(Exception):
  pass

class FileTooShortError(Error):
  pass

class HeightmapFileNotFound(Error):
  pass

class UnexpectedColumnCountError(Error):
  pass

class UnexpectedTokenCountError(Error):
  pass

def parse_args() -> argparse.Namespace:
  """Parses program arguments."""
  parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
  parser.add_argument('--input', required=True, help='Input height.map path')
  parser.add_argument('--offset', required=True, type=float, help='Z offset to apply.')
  return parser.parse_args()

def check_token_count(lines: List[str], index: int, expected_count: int):
  """Asserts that a given line has the expected token count."""
  actual_count = len(lines[index].split(';'))
  if actual_count != expected_count:
    raise UnexpectedTokenCountError(
        'Line %d has an unexpected number of tokens.  Expected %d, got %d' % (
          index + 1, expected_count, actual_count))

def candle_heightmap_adjust() -> None:
  """Main logic."""
  args = parse_args()
  input_path = pathlib.Path(args.input)
  if not input_path.exists():
    raise HeightmapFileNotFound('%s does not exist.' % input_path)

  with input_path.open(encoding='utf8') as fin:
    lines = [l.strip() for l in fin if l.strip()]

  if len(lines) < 4:
    raise FileTooShortError('Heightmap file is too short to be valid')

  # Validate file format expectations.
  check_token_count(lines, 0, 4)
  check_token_count(lines, 1, 4)
  check_token_count(lines, 2, 3)
  rows_and_cols = lines[2].split(';')
  cols = int(rows_and_cols[1])
  rows = int(rows_and_cols[2])

  if len(lines) != (rows + 3):
    raise FileTooShortError(
        'With %d rows, expected %d lines in the file.  '
        'Found %d lines instead' % (rows, rows + 3, len(lines)))

  new_lines = lines[:3]
  for line in lines[3:]:
    tokens = line.split(';')
    if len(tokens) != cols:
      raise UnexpectedColumnCountError(
          'Expected %d columns, found %d' % (cols, len(tokens)))
    new_lines.append(';'.join(str(float(t) + args.offset) for t in tokens))

  # create an output file in the same directory.
  output_path = pathlib.Path(
      input_path.parents[0],
      '%s_offset%s%s' % (input_path.stem, args.offset, input_path.suffix))
  output_path.write_text('\n'.join(new_lines), encoding='utf8')
  print('Wrote %s' % output_path)

def main() -> None:
  """Program entry."""
  try:
    candle_heightmap_adjust()
  except Error as e:
    sys.exit(e)

if __name__ == '__main__':
  main()
