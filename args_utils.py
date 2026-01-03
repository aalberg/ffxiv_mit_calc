import argparse

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
  parser.add_argument('-k', type=bool)
  return parser.parse_args()
