import csv, hashlib, io, json, math, re
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from .validation import validate_input, http_url, unique

def now(): return datetime.now(timezone.utc).isoformat()
def validate(data,records): return initialize(validate_input(data,CONFIG['example']),records)

def plan(text):
    try: graph=json.loads(text)
    except ValueError: raise ValueError('Graph must be valid JSON')
    if not isinstance(graph,dict) or not graph: raise ValueError('Graph must be a nonempty object')
    if any(not node or not isinstance(deps,list) or any(not isinstance(dep,str) or dep not in graph for dep in deps) for node,deps in graph.items()): raise ValueError('Every dependency must name an existing resource')
    order=[]; pending=set(graph)
    while pending:
        ready=sorted(node for node in pending if all(dep in order for dep in graph[node]))
        if not ready: raise ValueError('Dependency cycle detected')
        order.extend(ready); pending.difference_update(ready)
    return order
def initialize(row,records):
    order=plan(row['graph'])
    return dict(row,status='draft',resource_count=len(order),order=[])
def summary(rows): return {'stacks':len(rows),'resources':sum(r['resource_count'] for r in rows),'planned':sum(r['status']=='planned' for r in rows)}
def transition(row,action):
    if action!='plan': raise ValueError('Unsupported action')
    return dict(row,status='planned',order=plan(row['graph']))
