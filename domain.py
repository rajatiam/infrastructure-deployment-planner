import csv, hashlib, io, json, math, re
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def now(): return datetime.now(timezone.utc).isoformat()

def validate(data, records):
    if not isinstance(data,dict): raise ValueError('JSON object required')
    row = {}
    for key,example in CONFIG['example'].items():
        value = data.get(key)
        if isinstance(example,bool):
            if not isinstance(value,bool): raise ValueError(key+' must be boolean')
        elif isinstance(example,(int,float)):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0: raise ValueError(key+' must be finite and nonnegative')
            if isinstance(example,int) and not isinstance(value,int): raise ValueError(key+' must be an integer')
        elif not isinstance(value,str) or not value.strip() or len(value)>2000: raise ValueError(key+' requires text, up to 2000 characters')
        row[key] = value.strip() if isinstance(value,str) else value
    return initialize(row,records)

def http_url(value):
    url = urlparse(value)
    if url.scheme not in ['http','https'] or not url.hostname or url.username or url.password: raise ValueError('HTTP(S) URL without credentials required')

def unique(rows,row,fields):
    if any(all(r[f]==row[f] for f in fields) for r in rows): raise ValueError('Duplicate '+', '.join(fields))

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
