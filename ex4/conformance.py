from datetime import datetime
import xml.etree.ElementTree as ET
from itertools import combinations


class GraphDiscovery:
    def __init__(self):
        pass

    def read_from_file(self, filename):
        def tag(element):
            return element.tag.rsplit("}", 1)[-1]

        def read_attr(attr):
            key = attr.get("key")
            value = attr.get("value")
            if not key or not key.strip() or value is None:
                raise ValueError("Missing XES key or value")

            kind = tag(attr)
            if kind == "date":
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                value = value.replace(tzinfo=None)
            elif kind == "int":
                value = int(value)
            elif kind == "float":
                value = float(value)
            elif kind == "boolean":
                if value not in ("true", "false", "1", "0"):
                    raise ValueError("Invalid XES boolean")
                value = value in ("true", "1")
            return key, value

        root = ET.parse(filename).getroot()
        cases = {}
        for trace in root:
            if tag(trace) != "trace":
                continue

            case_id = None
            for attr in trace:
                if tag(attr) == "event":
                    continue
                key, value = read_attr(attr)
                if key == "concept:name":
                    case_id = value
            if not isinstance(case_id, str) or not case_id.strip():
                raise ValueError("Missing case ID")

            events = []
            for event in trace:
                if tag(event) != "event":
                    continue
                data = {}
                for attr in event:
                    key, value = read_attr(attr)
                    data[key] = value
                events.append(data)
            cases[case_id] = events
        return cases


class PetriNet:
    def __init__(self):
        #Initializing
        #set of places P as an hashset (id)
        self.places = set()

        #set of transitions T hashmap (name, id)
        self.transitions = {}
        self.name_to_id = {}

        #flow relation is two adjacency maps (for pre and post)
        self.pre = {}
        self.post = {}

        #tokens is an hashmap (place, token quantity)
        self.tokens = {}

    def add_place(self, name):
        self.places.add(name)
        self.tokens[name] = 0

    def add_transition(self, name, id):
        self.transitions[id] = name
        self.name_to_id[name] = id

    def transition_name_to_id(self, name):
        for k, v in self.transitions.items():
            if v == name:
                return k
        raise KeyError(name)

    def add_edge(self, source, target):

        if target not in self.pre:
            self.pre[target] = set()
        if source not in self.post:
            self.post[source] = set()

        self.pre[target].add(source)
        self.post[source].add(target)

        return self

    def get_tokens(self, place):
        return self.tokens.get(place, 0)

    def is_enabled(self, transition):
        for source in self.pre.get(transition, set()):
            if self.tokens.get(source, 0) < 1:
                return False
        return True

    def add_marking(self, place):
        self.tokens[place] = self.tokens.get(place, 0) + 1

    def fire_transition(self, transition):
        #If the transition is enabled, remove one token from each input place and add one token to each output place
        if self.is_enabled(transition):
            for source in self.pre.get(transition, set()):
                self.tokens[source] -= 1

            for target in self.post.get(transition, set()):
                self.tokens[target] = self.tokens.get(target, 0) + 1


def alpha(log):
    activities = set()

    #collected distinct activities with a set
    for case in log.values():
        for event in case:
            activities.add(event["concept:name"])

    activities = sorted(activities)

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

            pairs.add((a, b))

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


_graph_discovery = GraphDiscovery()


def read_from_file(filename):
    return _graph_discovery.read_from_file(filename)
