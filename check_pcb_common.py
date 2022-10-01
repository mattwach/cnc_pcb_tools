"""Common checks that would go in every file."""

def check_common(check):
  """Common checks that would otherwise have to be repeated in every file."""
  check.dump_properties()
  check.assert_spinning()
  # Assumes a 7x10cm board with the origin at the upper-left
  check.assert_gt('min_x', check.min_x(), -2.0)
  check.assert_lt('max_x', check.max_x(), 100.0)
  check.assert_gt('min_y', check.min_y(), -70.0)
  check.assert_lt('max_y', check.max_y(), 2.0)

  # maximum allowed z
  check.assert_lt('max_z', check.max_z(), 15.1)
