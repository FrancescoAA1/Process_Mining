import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ex2.graph_discovery import read_from_file
from ex1.petri_net import PetriNet

def alpha(log):
    activities = set()

    #collected distinct activities with a set
    for case in log.values():
        for event in case:
            activities.add(event["concept:name"])

    p = PetriNet()

    #created transitions
    for i, a in enumerate(activities):
        p.add_transition(a, i)

    pairs = set()

    #started scanning each case to get direct-follow pairs
    for case in log.values():
        for i in range(len(case) - 1):
            a = case[i]["concept:name"]
            b = case[i + 1]["concept:name"]

            pairs.add((a,b))


    def causal(a, b):
        return (a, b) in pairs and (b, a) not in pairs

    def compatible(candidate):
        X, Y = candidate

        for x in X:
            for y in Y:
                if not causal(x, y):
                    return False

        for x1 in X:
            for x2 in X:
                if x1 != x2 and ((x1, x2) in pairs or (x2, x1) in pairs):
                    return False

        for y1 in Y:
            for y2 in Y:
                if y1 != y2 and ((y1, y2) in pairs or (y2, y1) in pairs):
                    return False

        return True

    place_candidates = set()

    #define place candidates
    for a in activities:
        for b in activities:
            if a == b:
                continue
            
            ab = (a, b) in pairs
            ba = (b, a) in pairs

            if ab and not ba:
                place_candidates.add((frozenset({a}), frozenset({b})))
            continue

    changed = True

    while changed:
        changed = False
        new_candidates = set(place_candidates)
        candidates_list = list(place_candidates)

        for i in range(len(candidates_list)):
            for j in range(i + 1, len(candidates_list)):
                X1, Y1 = candidates_list[i]
                X2, Y2 = candidates_list[j]

                merged = (X1 | X2, Y1 | Y2)

                if merged not in new_candidates and compatible(merged):
                    new_candidates.add(merged)
                    changed = True

        place_candidates = new_candidates

    #remove non-maximal candidates
    maximal_candidates = set()

    for c1 in place_candidates:
        X1, Y1 = c1
        is_maximal = True

        for c2 in place_candidates:
            if c1 == c2:
                continue

            X2, Y2 = c2

            if X1 <= X2 and Y1 <= Y2:
                is_maximal = False
                break

        if is_maximal:
            maximal_candidates.add(c1)

    place_candidates = maximal_candidates

    start_activities = {case[0]["concept:name"] for case in log.values() if case}
    end_activities = {case[-1]["concept:name"] for case in log.values() if case}

    start_place = "__start__"
    end_place = "__end__"

    p.add_place(start_place)
    p.add_marking(start_place)
    p.add_place(end_place)

    for activity in start_activities:
        p.add_edge(start_place, p.transition_name_to_id(activity))

    for X, Y in place_candidates:
        place_id = f"p_{len(p.places)}"
        while place_id in p.places:
            place_id = f"p_{len(p.places)}_{len(X)}_{len(Y)}"

        p.add_place(place_id)

        for x in X:
            p.add_edge(p.transition_name_to_id(x), place_id)

        for y in Y:
            p.add_edge(place_id, p.transition_name_to_id(y))

    for activity in end_activities:
        p.add_edge(p.transition_name_to_id(activity), end_place)

    return p


if __name__ == "__main__":
    mined_model = alpha(read_from_file(str(Path(__file__).with_name("extension-log-3.xes"))))

    def check_enabled(pn):
        ts = ["record issue", "inspection", "intervention authorization", "action not required", "work mandate", "no concession", "work completion", "issue completion"]
        for t in ts:
            print(pn.is_enabled(pn.transition_name_to_id(t)))
        print("")

    trace = ["record issue", "inspection", "intervention authorization", "work mandate", "work completion", "issue completion"]
    for a in trace:
        check_enabled(mined_model)
        mined_model.fire_transition(mined_model.transition_name_to_id(a))