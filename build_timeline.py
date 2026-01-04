from collections import defaultdict

import args_utils

from fflogs_secrets import CLIENT_ID, CLIENT_SECRET
from fflogsapi.util.gql_enums import GQLEnum
from fflogsapi import FFLogsClient

args = args_utils.parse_args()
print(args)
client = FFLogsClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

print(f"Fetching report: {args.r}...")
report = client.get_report(args.r)

# We need to get the master list of abilities to map ability IDs back to names
# later.
abilities = {}
for a in report.abilities():
  #print("ability", a.game_id, a)
  abilities[a.game_id] = a

print("Processing pulls...")


def aid_to_name(aid):
  return abilities[aid].name


def print_event(event, damage_for_event, fight_start):
  time_delta = event['timestamp'] - fight_start
  print(";".join([
      args_utils.milli_to_pretty(time_delta),
      aid_to_name(event['abilityGameID']),
      str(event['abilityGameID']),
      str(len(damage_for_event))
  ] + [str(i) for i in damage_for_event]))


for fight in report:
  if args.n and fight.id not in args.n:
    continue
  if args.k and not fight.is_kill():
    continue
  # Skip very short pulls (less than 30 seconds)
  if not fight or (fight.end_time() - fight.start_time()) < 30000:
    continue

  STATUS = "KILL" if fight.is_kill() else "WIPE"
  print(f"\nPull {fight.id}: {fight.name()} ({STATUS})")
  #print(fight.start_time(), fight.end_time())

  # The fight start is triggered when the first prepares event occurs prepull,
  # but the 0:00 point is marked by the LB reset on combat start.
  lb_events = fight.events(
      filters={"filterExpression": "type=\"limitbreakupdate\""})
  real_fight_start = lb_events[0]['timestamp']

  enemy_events = fight.events(filters={"dataType": GQLEnum("DamageTaken")})
  current_event = None
  events_in_flight = defaultdict(int)
  damage_for_event = []
  for e in enemy_events:
    if not args.a and aid_to_name(e['abilityGameID']) == "Attack":
      continue
    #print(e)
    event_key = (e['abilityGameID'], e['sourceID'], e['targetID'])
    if e['type'] == 'calculateddamage':
      if not current_event:
        current_event = e
      events_in_flight[event_key] += 1
      #print("added", event_key)
      # This is a new event, so reset things to keep old events from polluting
      # the list of in flight events
      if not args.d and not (e['timestamp'] == current_event['timestamp'] and
                             e['sourceID'] == current_event['sourceID']):
        #if sum(events_in_flight.values()):
        #  print('nuking', event_key)
        #events_in_flight = defaultdict(int)
        #damage_for_event = []
        print_event(current_event, [], real_fight_start)
      current_event = e
    elif args.d and e['type'] == 'damage':  # This breaks under a lot of cases
      if event_key not in events_in_flight:
        #if aid_to_name(e['abilityGameID']) not in ["Combined DoTs", "Sustained Damage"]:
        if 'tick' not in e or not e['tick']:
          print('error: missing key:', event_key,
                aid_to_name(e['abilityGameID']), e)
        continue
      #print(e)
      if 'unmitigatedAmount' in e:
        damage_for_event.append(e['unmitigatedAmount'])
      #print("removed", event_key)
      events_in_flight[event_key] -= 1
      if 'overkill' in e or not events_in_flight[event_key]:
        #print("done", event_key)
        del events_in_flight[event_key]
      # All the current events are done, so flush the log line and reset
      #print(events_in_flight)
      if sum(events_in_flight.values()) == 0:
        print_event(current_event, damage_for_event, real_fight_start)
        damage_for_event = []
  if not args.d:
    print_event(current_event, [], real_fight_start)
