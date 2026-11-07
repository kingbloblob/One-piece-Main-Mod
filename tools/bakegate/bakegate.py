"""Static bake gate: blockstate -> model -> parent -> textures, item defs, lang. Usage: bakegate.py <resources/assets> <vanilla client jar>"""
import json, os, sys, zipfile, collections

ASSETS, JAR = sys.argv[1], sys.argv[2]
vanilla = set(n for n in zipfile.ZipFile(JAR).namelist() if n.startswith('assets/'))
vz = zipfile.ZipFile(JAR)
problems = collections.defaultdict(list)


def rl(ref, kind):
    ns, _, path = ref.partition(':') if ':' in ref else ('minecraft', None, ref)
    return ns, path


def find(ns, rel):
    p = os.path.join(ASSETS, ns, rel)
    if os.path.isfile(p):
        return ('mod', p)
    if f'assets/{ns}/{rel}' in vanilla:
        return ('van', f'assets/{ns}/{rel}')
    return None


def load(hit):
    if hit[0] == 'mod':
        with open(hit[1], encoding='utf-8') as f:
            return json.load(f)
    return json.loads(vz.read(hit[1]))


model_cache = {}


def check_model(ref, who):
    """Returns error string or None."""
    if ref in model_cache:
        return model_cache[ref]
    chain, textures, elements, cur, err = [], {}, None, ref, None
    while cur and not cur.startswith('builtin/'):
        ns, path = rl(cur, 'models')
        hit = find(ns, f'models/{path}.json')
        if not hit:
            err = f'missing model {ns}:{path}' + (f' (parent of {chain[-1]})' if chain else '')
            break
        try:
            m = load(hit)
        except Exception as e:
            err = f'bad json {hit[1]}: {e}'
            break
        chain.append(cur)
        for k, v in (m.get('textures') or {}).items():
            textures.setdefault(k, v)
        if elements is None and 'elements' in m:
            elements = m['elements']
        cur = m.get('parent')
        if len(chain) > 30:
            err = 'parent loop'
            break
    if not err:
        def resolve(v, depth=0):
            while isinstance(v, str) and v.startswith('#') and depth < 20:
                v = textures.get(v[1:]); depth += 1
            return v
        used = set()
        for el in elements or []:
            for face in (el.get('faces') or {}).values():
                used.add(face.get('texture'))
        if 'particle' in textures:
            used.add('#particle')
        for t in list(textures.values()) + list(used):
            if not isinstance(t, str):
                continue
            r = resolve(t)
            if r is None:
                err = f'texture variable {t} never set'
                break
            if isinstance(r, dict):
                r = r.get('sprite')
            ns, path = rl(r, 'textures')
            if not find(ns, f'textures/{path}.png'):
                err = f'missing texture {ns}:{path}'
                break
    model_cache[ref] = err
    return err


def walk_models(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == 'model' and isinstance(v, str):
                out.append(v)
            else:
                walk_models(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_models(v, out)


lang = {}
for ns in os.listdir(ASSETS):
    p = os.path.join(ASSETS, ns, 'lang', 'en_us.json')
    if os.path.isfile(p):
        with open(p, encoding='utf-8') as f:
            lang.update(json.load(f))

counts = collections.Counter()
for ns in sorted(os.listdir(ASSETS)):
    for kind in ('blockstates', 'items'):
        d = os.path.join(ASSETS, ns, kind)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.json'):
                continue
            name = fn[:-5]
            counts[kind] += 1
            try:
                with open(os.path.join(d, fn), encoding='utf-8') as f:
                    j = json.load(f)
            except Exception as e:
                problems[kind].append(f'{ns}:{name}: bad json {e}')
                continue
            refs = []
            walk_models(j, refs)
            if not refs and kind == 'blockstates':
                problems[kind].append(f'{ns}:{name}: no models listed')
            for r in sorted(set(refs)):
                e = check_model(r, name)
                if e:
                    problems[kind].append(f'{ns}:{name}: {e}')

# Registered names per lang: every item/block with a name should have an item def / blockstate.
for key in lang:
    parts = key.split('.')
    if len(parts) != 3 or parts[0] not in ('item', 'block'):
        continue
    kind, ns, name = parts
    if not ns.startswith('onepiece'):
        continue
    if kind == 'block' and not os.path.isfile(os.path.join(ASSETS, ns, 'blockstates', name + '.json')):
        problems['block with no blockstate (invisible/purple)'].append(f'{ns}:{name}')
    if kind == 'item' and not os.path.isfile(os.path.join(ASSETS, ns, 'items', name + '.json')):
        problems['item with no item definition (no icon)'].append(f'{ns}:{name}')
for ns in os.listdir(ASSETS):
    d = os.path.join(ASSETS, ns, 'items')
    if os.path.isdir(d):
        for fn in os.listdir(d):
            n = fn[:-5]
            if f'item.{ns}.{n}' not in lang and f'block.{ns}.{n}' not in lang:
                problems['item with no English name'].append(f'{ns}:{n}')

print('checked', dict(counts), 'models', len(model_cache))
for k, v in problems.items():
    print(f'\n== {k}: {len(v)}')
    for line in v[:400]:
        print('  ', line)
