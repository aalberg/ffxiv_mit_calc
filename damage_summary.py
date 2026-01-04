import args_utils

from fflogs_secrets import CLIENT_ID, CLIENT_SECRET
from fflogsapi.util.gql_enums import GQLEnum

from fflogsapi import FFLogsClient

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
  duration = (fight.end_time() - fight.start_time()) / 1000.0

  ### Start bad logic for filtering
  targetability = fight.events(
      filters={"filterExpression": "type=\"targetabilityupdate\""})
  if not targetability:
    continue
  end_p1 = targetability[0]["timestamp"]
  duration2 = (end_p1 - fight.start_time()) / 1000.0

  table = fight.table(filters={
      "dataType": GQLEnum("DamageDone"),
      "endTime": end_p1
  })
  ### End bad logic for filtering

  # Build the pretty table
  STATUS = "KILL" if fight.is_kill() else "WIPE"
  print(f"\nPull {fight.id}: {fight.name()} ({STATUS})")
  #print(f"{'Player':<15} | {'rDPS':<8} | {'aDPS':<8} | {'nDPS':<8}")
  #print("-" * 55)

  #print('entry:', table['entries'])
  new_table = []
  for entry in table['entries']:
    name = entry.get('name', 'Unknown')
    job = entry.get('type', 'idk')
    adps = entry.get('totalADPS', 0) / duration2
    rdps = entry.get('totalRDPS', 0) / duration2
    ndps = entry.get('totalNDPS', 0) / duration2

    # Filter out Limit Breaks or non-player entities if needed
    if entry.get('type') != "LimitBreak":
      new_table.append([adps, [str(i) for i in [job, adps, rdps]]])
      #print(";".join(str(i) for i in [name, adps, rdps]))
      #print(f"{name:<15} | {rdps:<8.1f} | {adps:<8.1f} | {ndps:<8.1f}")
  new_table = sorted(new_table, reverse=True)
  for t in new_table:
    print(";".join(t[1]))
