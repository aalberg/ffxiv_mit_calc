import args_utils

from fflogsapi import FFLogsClient
from fflogs_secrets import CLIENT_ID, CLIENT_SECRET

args = args_utils.parse_args()
client = FFLogsClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

print(f"Fetching report: {args.r}...")
report = client.get_report(args.r)

print("Processing pulls...")
for fight in report:
  if args.n and fight.id not in args.n:
    continue
  if args.k and not fight.is_kill():
    continue
  # Skip very short pulls (less than 30 seconds)
  if not fight or (fight.end_time() - fight.start_time()) < 30000:
    continue

  # The fight start is triggered when the first prepares event occurs prepull,
  # but the 0:00 point is marked by the LB reset on combat start.
  lb_events = fight.events(
      filters={"filterExpression": "type=\"limitbreakupdate\""})
  real_fight_start = lb_events[0]['timestamp']

  STATUS = "KILL" if fight.is_kill() else "WIPE"
  print(f"\nPull {fight.id}: {fight.name()} ({STATUS})")

  targetability = fight.events(
      filters={"filterExpression": "type=\"targetabilityupdate\""})
  if not targetability:
    continue
  ranges = []
  start_times = {}
  for e in targetability:
    eid = e['sourceID']
    timestamp = e['timestamp']
    if e['targetable']:
      start_times[eid] = timestamp
    else:
      s = start_times[eid] if eid in start_times else real_fight_start
      ranges.append((s, timestamp))

  if start_times:
    min_start = min(start_times.values())
    if min_start != real_fight_start:
      ranges.append((min_start, fight.end_time()))

  print(f"https://www.fflogs.com/reports/{args.r}?fight={fight.id}"
        "&type=damage-done")
  for r in ranges:
    print(f"https://www.fflogs.com/reports/{args.r}?fight={fight.id}"
          f"&type=damage-done&start={r[0]}&end={r[1]}")
