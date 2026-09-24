from ex2.graph_discovery import read_from_file
from ex1.petri_net import PetriNet

def alpha(log):
    activities = set()

    for case in log.values():
        for event in case:
            activities.add(event["concept:name"])

    p = PetriNet()

    for i, a in enumerate(activities):
        p.add_transition(a, i)

    pairs = set()

    for case in log.values():
        for i in range(len(case) - 1):
            a = case[i]["concept:name"]
            b = case[i + 1]["concept:name"]

            pairs.add((a,b))


if __name__ == "__main__":
    mined_model = alpha(read_from_file("extension-log.xes"))

def check_enabled(pn):
  ts = ["record issue", "inspection", "intervention authorization", "action not required", "work mandate", "no concession", "work completion", "issue completion"]
  for t in ts:
    print (pn.is_enabled(pn.transition_name_to_id(t)))
  print("")


trace = ["record issue", "inspection", "intervention authorization", "work mandate", "work completion", "issue completion"]
for a in trace:
  check_enabled(mined_model)
  mined_model.fire_transition(mined_model.transition_name_to_id(a))