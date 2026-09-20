import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
import xml.etree.ElementTree as ET


class GraphDiscovery:

    def __init__(self):
        pass

    def log_as_dictionary(self, log):
        cases = {}

        # Read event row 1 by 1
        for line in log.splitlines():
            line = line.strip()

            if not line:
                continue

            row = [value.strip() for value in line.split(";")]

            if len(row) != 4:
                raise ValueError("Malformed CSV row")

            activity, case_id, resource, timestamp = row

            if not activity or not case_id or not resource or not timestamp:
                raise ValueError("Malformed CSV row")

            event = {
                "concept:name": activity,
                "case:concept:name": case_id,
                "org:resource": resource,
                "time:timestamp": datetime.strptime(
                    timestamp, "%Y-%m-%d %H:%M:%S"
                ),
            }

            cases.setdefault(case_id, []).append(event)

        return cases

    def dependency_graph_inline(self, log):
        # count direct-follow pairs
        graph = {}
        for events in log.values():
            for i in range(len(events) - 1):
                first = events[i]["concept:name"]
                second = events[i + 1]["concept:name"]
                if first not in graph:
                    graph[first] = {}
                if second not in graph[first]:
                    graph[first][second] = 0
                graph[first][second] += 1
        return graph

    def read_from_file(self, filename):
        def tag(element):
            return element.tag.rsplit("}", 1)[-1]

        def read_attr(attr):
            key = attr.get("key")
            value = attr.get("value")
            if not key or not key.strip() or value is None:
                raise ValueError("Missing XES key or value")

            # convert XES values to py types
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

    def dependency_graph_file(self, log):
        return self.dependency_graph_inline(log)


# Class methods for Autolab checker
_graph_discovery = GraphDiscovery()


def log_as_dictionary(log):
    return _graph_discovery.log_as_dictionary(log)


def dependency_graph_inline(log):
    return _graph_discovery.dependency_graph_inline(log)


def read_from_file(filename):
    return _graph_discovery.read_from_file(filename)


def dependency_graph_file(log):
    return _graph_discovery.dependency_graph_file(log)




if __name__ == "__main__":
    discovery = GraphDiscovery()
    log = discovery.read_from_file(Path(__file__).with_name("extension-log.xes"))

    for case_id in sorted(log):
        print((case_id, len(log[case_id])))

    event = log["case_123"][0]
    print((
        event["concept:name"],
        event["org:resource"],
        event["time:timestamp"],
        event["cost"],
    ))