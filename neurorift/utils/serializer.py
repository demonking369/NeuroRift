import json


def dumps(v):
    return json.dumps(v, indent=2, default=str)
