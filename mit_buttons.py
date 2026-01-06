from collections import defaultdict

import args_utils

from fflogsapi import FFLogsClient
from fflogs_secrets import CLIENT_ID, CLIENT_SECRET

MIT_NAMES = [
    # Tank
    "Reprisal",
    "Passage of Arms",
    "Divine Veil",
    "Shake It Off",
    "Dark Missionary",
    "Heart of Light",
    # Melee"
    "Feint",
    "Riddle of Earth",
    "Shade Shift",
    "Tengentsu",
    "Arcane Crest",
    "Second Wind"
    # Phys ranged
    "Troubadour",
    # "Nature's Minne", This doesn't work for some reason, use the id instead
    "Tactician",
    "Dismantle",
    "Shield Samba",
    "Improvisation",
    # # Caster
    "Addle",
    "Manaward",
    "Radiant Aegis",
    "Magick Barrier",
    "Tempera Coat",
    "Tempera Grassa",
    # Healer
    # WHM
    "Plenary Indulgence",
    "Temperance",
    "Liturgy of the Bell",
    "Divine Caress",
    # SCH
    "Sacred Soil",
    "Expedient",
    "Deployment Tactics",
    "Summon Seraph",
    "Seraphism",
    "Fey Illumination",
    # AST
    "Collective Unconscious",
    "Neutral Sect",
    "Sun Sign",
    "Macrocosmos",
    # SGE
    "Kerachole",
    "Holos",
    "Panhaima",
    "Philosophia",
]
FILTER_STRING = ("type=\"cast\" and (ability.id=7408 or " +
                 " or ".join([f"ability.name=\"{a}\"" for a in MIT_NAMES]) +
                 ")")

args = args_utils.parse_args()
client = FFLogsClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

print(f"Fetching report: {args.r}...")
report = client.get_report(args.r)

# We need to get the master list of abilities to map ability IDs back to names
# later.
abilities = {}
for a in report.abilities():
  abilities[a.game_id] = a

# Also load the players
players = {}
for a in report.actors():
  if a.type == "Player" and a.id not in players:
    players[a.id] = a


def aid_to_name(aid):
  return abilities[aid].name


# Annotate rep and feint.
def annotate_event(e):
  name = aid_to_name(e['abilityGameID'])
  if name in ("Reprisal", "Feint", "Addle"):
    return name + " " + players[e['sourceID']].name
  return name


def print_event(e, fight_start):
  time_delta = e['timestamp'] - fight_start
  print(args_utils.milli_to_pretty(time_delta), annotate_event(e))


print("Processing pulls...")
for fight in (report if args.n else [report.fight()]):
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

  mit_events = fight.events(filters={"filterExpression": FILTER_STRING})
  if not mit_events:
    continue
  if not args.c:
    for e in mit_events:
      print_event(e, real_fight_start)
  else:
    collected_events = defaultdict(list)
    for e in mit_events:
      time_delta = e['timestamp'] - real_fight_start
      collected_events[annotate_event(e)].append(args_utils.milli_to_pretty(time_delta))
    for button, times in sorted(collected_events.items()):
      print(button)
      for t in times:
        print(t)
      print("")
  # ranges = []
  # start_times = {}
  # for e in targetability:
  #   eid = e['sourceID']
  #   timestamp = e['timestamp']
  #   if e['targetable']:
  #     start_times[eid] = timestamp
  #   else:
  #     s = start_times[eid] if eid in start_times else real_fight_start
  #     ranges.append((s, timestamp))

  # if start_times:
  #   min_start = min(start_times.values())
  #   if min_start != real_fight_start:
  #     ranges.append((min_start, fight.end_time()))

  # print(f"https://www.fflogs.com/reports/{args.r}?fight={fight.id}"
  #       "&type=damage-done")
  # for r in ranges:
  #   print(f"https://www.fflogs.com/reports/{args.r}?fight={fight.id}"
  #         f"&type=damage-done&start={r[0]}&end={r[1]}")
