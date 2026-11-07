import json, os, re, gzip, struct, sys
V='/tmp/claude-0/vanilla'; RES='/tmp/claude-0/sync/one-piece-mod/src/main/resources'
reg=json.load(open(f'{V}/reg.json')); blocks=json.load(open(f'{V}/blocks.json'))
allnames=set()
for k,v in reg.items(): allnames.update(v)
# vanilla tags known
tagnames=set()
for k,v in reg.items():
    if k.startswith('tag/'): tagnames.update(v)
OURS_BLOCKS={'seastone_ore','deepslate_seastone_ore','seastone_block','adam_log','adam_planks','island_cloud','sea_cloud'}
OURS_ITEMS=OURS_BLOCKS|{'raw_seastone','seastone_ingot','seastone_jitte','seastone_cuffs','berry','gomu_gomu_no_mi'}
problems=[]
ours_files=set()
for root,_,fs in os.walk(f'{RES}/data/onepiece'):
    for f in fs: ours_files.add(os.path.relpath(os.path.join(root,f),f'{RES}/data/onepiece'))
def onepiece_exists(n):
    if n in OURS_ITEMS: return True
    for f in ours_files:
        if f.split('/',1)[-1].rsplit('.',1)[0]==n or re.sub(r'^(worldgen/)?[a-z_]+/','',f).rsplit('.',1)[0]==n: return True
    if n.startswith('chests/') or n.startswith('blocks/'): return True
    return n.startswith('grand_line') or n.endswith('/start') or 'has_structure' in n
for root,_,fs in os.walk(f'{RES}/data'):
    for f in fs:
        if not f.endswith('.json'): continue
        p=os.path.join(root,f); txt=open(p).read(); json.loads(txt)
        if '/density_function/' in p: continue
        for m in re.findall(r'"#?(minecraft|onepiece):([a-z0-9_/.]+)', txt):
            ns,n=m
            if ns=='minecraft' and n not in allnames and n not in tagnames:
                problems.append((p.replace(RES,''),'unknown minecraft:'+n))
            if ns=='onepiece' and not onepiece_exists(n):
                problems.append((p.replace(RES,''),'unknown onepiece:'+n))
# NBT reader
def rd(b,i,t):
    if t==1: return struct.unpack_from('>b',b,i)[0],i+1
    if t==3: return struct.unpack_from('>i',b,i)[0],i+4
    if t==5: return struct.unpack_from('>f',b,i)[0],i+4
    if t==6: return struct.unpack_from('>d',b,i)[0],i+8
    if t==8:
        n=struct.unpack_from('>H',b,i)[0]; return b[i+2:i+2+n].decode(),i+2+n
    if t==9:
        et,n=struct.unpack_from('>bi',b,i); i+=5; out=[]
        for _ in range(n): v,i=rd(b,i,et); out.append(v)
        return out,i
    if t==10:
        out={}
        while True:
            tt=b[i]; i+=1
            if tt==0: return out,i
            n=struct.unpack_from('>H',b,i)[0]; k=b[i+2:i+2+n].decode(); i+=2+n
            out[k],i=rd(b,i,tt)
for root,_,fs in os.walk(f'{RES}/data/onepiece/structure'):
    for f in fs:
        b=gzip.open(os.path.join(root,f)).read(); d,_=rd(b,3+0,10) if False else rd(b,3,10)
        for e in d['palette']:
            ns,n=e['Name'].split(':')
            if ns=='onepiece':
                if n not in OURS_BLOCKS: problems.append((f,'bad block '+e['Name']))
                continue
            if n not in blocks: problems.append((f,'unknown block '+n)); continue
            props=blocks[n][0]
            for k,v in e.get('Properties',{}).items():
                if k not in props or v not in props[k]: problems.append((f,f'bad prop {n}[{k}={v}]'))
        for en in d['entities']:
            eid=en['nbt']['id']
            if eid!='onepiece:character' and eid.split(':')[1] not in reg['entity_type']: problems.append((f,'bad entity '+eid))
        for blk in d['blocks']:
            if 'nbt' in blk and 'LootTable' in blk['nbt']:
                lt=blk['nbt']['LootTable'].split(':')[1]
                if not os.path.exists(f'{RES}/data/onepiece/loot_table/{lt}.json'): problems.append((f,'missing loot '+lt))
        sz=d['size']
        if max(sz)>128: problems.append((f,'big '+str(sz)))
print('\n'.join(map(str,problems)) or 'ALL OK')
