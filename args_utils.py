import argparse

def milli_to_pretty(ms):
  return f"{ms // 60000}:{((ms % 60000) / 1000):06.3f}"

def parse_range(astr):
  result = set()
  for part in astr.split(','):
    x = part.split('-')
    result.update(range(int(x[0]), int(x[-1]) + 1))
  return sorted(result)

def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-r', type=str)
  parser.add_argument('-n', type=parse_range)
  parser.add_argument('-k', action='store_true')
  parser.add_argument('-a', action='store_true')
  parser.add_argument('-d', action='store_true')
  parser.add_argument('-c', action='store_true')
  return parser.parse_args()
