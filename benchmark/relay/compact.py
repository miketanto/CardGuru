import json, sys
d = json.load(open(f"/tmp/claude-501/llm-esc5/req-{sys.argv[1]}.json"))
r = d['request']
out = {"seq": d['seq'], "request": {k: v for k, v in r.items() if k != 'seq'}}
b = d.get('belief')
if b: out['belief'] = {k: b[k] for k in ('archetype', 'p', 'trick_rate') if k in b}
if d.get('card_reference'): out['card_reference'] = d['card_reference']
print(json.dumps(out))
