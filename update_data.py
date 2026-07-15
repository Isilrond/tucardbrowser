# -*- coding: utf-8 -*-
import urllib.request, json, os, traceback, re
import xml.etree.ElementTree as ET

BASE_URL     = 'http://mobile.tyrantonline.com/assets'
XML_SECTIONS = ['cards_section_%d.xml' % i for i in range(1, 22)]
XML_EXTRA    = ['skills_set.xml', 'fusion_recipes_cj2.xml']
ALL_XMLS     = XML_SECTIONS + XML_EXTRA
FACTION_MAP  = {'1':'Imperial','2':'Raider','3':'Bloodthirsty','4':'Xeno','5':'Righteous','6':'Progenitor'}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
XML_DIR    = os.path.join(SCRIPT_DIR, 'XMLS')
OUT_FILE   = os.path.join(SCRIPT_DIR, 'tu_data.json')
IMAGES_DIR = os.path.join(SCRIPT_DIR, 'images')

def fetch(url, label):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TU-Updater/1.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        print('  OK ' + label)
        return data
    except Exception as e:
        print('  FEHLER ' + label + ': ' + str(e))
        return None

def load_xml(fname):
    path = os.path.join(XML_DIR, fname)
    if not os.path.exists(path): return None
    with open(path, 'rb') as f: return f.read()

def parse_et(raw_bytes):
    text = raw_bytes.decode('utf-8', errors='replace').lstrip('\ufeff')
    if text.startswith('<?xml'):
        end = text.find('?>')
        if end != -1: text = text[end+2:].lstrip()
    # Escape bare & that are not valid XML entities
    text = re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+|#x[\da-fA-F]+);)', '&amp;', text)
    return ET.fromstring('<root>' + text + '</root>')

def gv(node, tag):
    c = node.find(tag)
    if c is not None and c.text: return c.text.strip()
    return node.get(tag)

def parse_skill(s):
    sid = s.get('id') or (s.text.strip() if s.text else None)
    if not sid: return None
    d = {'id': sid}
    for k in ('x','y','s','s2','n','c','all','trigger','card_id'):
        v = s.get(k)
        if v: d[k] = v
    return d

def parse_cards(raw_bytes):
    root = parse_et(raw_bytes)
    cards = []
    for unit in root.iter('unit'):
        uid = gv(unit,'id'); name = gv(unit,'name') or gv(unit,'n')
        if not uid or not name: continue
        type_id=gv(unit,'type') or '1'; set_id=gv(unit,'set') or '1000'
        picture=gv(unit,'picture') or ''; attack=gv(unit,'attack') or '0'
        health=gv(unit,'health') or '0'; cost=gv(unit,'cost') or '0'
        rarity=gv(unit,'rarity') or '1'; delay=gv(unit,'delay') or '0'
        fusion_lvl=gv(unit,'fusion_level') or '0'; asset_bndl=gv(unit,'asset_bundle') or ''
        set_num=int(set_id)
        uid_int=int(uid)
        if   uid_int < 1000:  unit_type='assault'
        elif uid_int < 2000:  unit_type='commander'
        elif uid_int < 3001:  unit_type='structure'
        elif uid_int < 7995:  unit_type='assault'
        elif uid_int < 10000: unit_type='structure'
        elif uid_int < 17000: unit_type='assault'
        elif uid_int < 25000: unit_type='structure'
        elif uid_int < 30000: unit_type='commander'
        elif uid_int < 50000: unit_type='assault'
        elif uid_int < 55001: unit_type='structure'
        else:                 unit_type='assault'
        skills=[s for s in (parse_skill(sk) for sk in unit.findall('skill')) if s]
        upgrades=[]; prev={'picture':picture,'attack':attack,'health':health,'cost':cost,'delay':delay,'fusion_level':fusion_lvl,'asset_bundle':asset_bndl}
        for upg in unit.findall('upgrade'):
            def p(tag, key, _u=upg, _p=dict(prev)): return gv(_u,tag) or _p[key]
            cid=gv(upg,'card_id'); level=gv(upg,'level')
            upg_pic=p('picture','picture'); upg_atk=p('attack','attack'); upg_hp=p('health','health')
            upg_cst=p('cost','cost'); upg_dly=p('delay','delay'); upg_fus=p('fusion_level','fusion_level'); upg_bnd=p('asset_bundle','asset_bundle')
            uskills=[s for s in (parse_skill(sk) for sk in upg.findall('skill')) if s]
            ul={'id':cid,'level':level,'picture':upg_pic,'attack':upg_atk,'health':upg_hp,'cost':upg_cst,'delay':upg_dly,'fusion_level':upg_fus,'asset_bundle':upg_bnd,'skills':uskills}
            upgrades.append(ul)
            prev={'picture':upg_pic,'attack':upg_atk,'health':upg_hp,'cost':upg_cst,'delay':upg_dly,'fusion_level':upg_fus,'asset_bundle':upg_bnd}
        max_level=int(upgrades[-1]['level'] or 1) if upgrades else 1
        cards.append({'id':uid,'name':name,'picture':picture,'attack':attack,'health':health,'cost':cost,'rarity':rarity,'type':type_id,'faction':FACTION_MAP.get(type_id,'Unknown'),'set':set_id,'delay':delay,'fusion_level':fusion_lvl,'asset_bundle':asset_bndl,'unit_type':unit_type,'skills':skills,'upgrades':upgrades,'max_level':max_level})
    return cards

def parse_skills(raw_bytes):
    root=parse_et(raw_bytes); names,descs,descs_all,descs_fac,descs_all_fac={},{},{},{},{}
    for node in root.iter('skillType'):
        sid=gv(node,'id'); name=gv(node,'name')
        if not sid or not name: continue
        names[sid]=name; descs[sid]=gv(node,'desc') or ''
        d_all=gv(node,'desc_all') or ''; d_fac=gv(node,'desc_faction') or ''; d_af=gv(node,'desc_all_faction') or ''
        if d_all: descs_all[sid]=d_all
        if d_fac: descs_fac[sid]=d_fac
        if d_af: descs_all_fac[sid]=d_af
    return names,descs,descs_all,descs_fac,descs_all_fac

def parse_fusions(raw_bytes):
    root=parse_et(raw_bytes); fusion_map={}
    for fr in root.iter('fusion_recipe'):
        cid=gv(fr,'card_id')
        if not cid: continue
        fusion_map[cid]=[{'card_id':r.get('card_id'),'number':r.get('number')} for r in fr.findall('resource')]
    return fusion_map

def build_derived(cards, fusion_map):
    id_to_name={}
    for c in cards:
        id_to_name[c['id']]=c['name']
        for u in c['upgrades']:
            if u.get('id'): id_to_name[u['id']]=c['name']
    fusion_from,fusion_to={},{}
    for rid,resources in fusion_map.items():
        for r in resources:
            iid=r.get('card_id','')
            if not iid: continue
            fusion_from.setdefault(rid,[]).append(iid); fusion_to.setdefault(iid,[]).append(rid)
    base_fusion_from={rid:[id_to_name.get(i,'ID:'+i) for i in ids] for rid,ids in fusion_from.items()}
    base_fusion_to={iid:[id_to_name.get(i,'ID:'+i) for i in ids] for iid,ids in fusion_to.items()}
    summoned_by={}
    for c in cards:
        for sk in c['skills']+[sk for u in c['upgrades'] for sk in u['skills']]:
            if sk.get('id')=='summon' and sk.get('card_id'):
                t=sk['card_id']; summoned_by.setdefault(t,[])
                if c['id'] not in summoned_by[t]: summoned_by[t].append(c['id'])
    return id_to_name,fusion_from,fusion_to,base_fusion_from,base_fusion_to,summoned_by

success = False
print('Tyrant Unleashed - tu_data.json Updater')
print('='*42)
try:
    os.makedirs(XML_DIR, exist_ok=True)
    print('\nDownloading XMLs to XMLS/ ...')
    ok=0
    for fname in ALL_XMLS:
        data=fetch(BASE_URL+'/'+fname,fname)
        if data:
            with open(os.path.join(XML_DIR,fname),'wb') as f: f.write(data)
            ok+=1
    print('  %d/%d heruntergeladen'%(ok,len(ALL_XMLS)))
    if ok==0: raise Exception('Keine XMLs - Internetverbindung pruefen')
    print('\nParsing skills...')
    skill_names,skill_descs,skill_descs_all,skill_descs_fac,skill_descs_all_fac={},{},{},{},{}
    raw=load_xml('skills_set.xml')
    if raw:
        skill_names,skill_descs,skill_descs_all,skill_descs_fac,skill_descs_all_fac=parse_skills(raw)
        print('  %d skills'%len(skill_names))
    print('Parsing fusions...')
    fusion_map={}
    raw=load_xml('fusion_recipes_cj2.xml')
    if raw:
        fusion_map=parse_fusions(raw)
        print('  %d recipes'%len(fusion_map))
    print('Parsing cards...')
    all_cards=[]
    for fname in XML_SECTIONS:
        raw=load_xml(fname)
        if raw:
            try:
                cards=parse_cards(raw); all_cards.extend(cards)
                print('  %s: %d'%(fname,len(cards)))
            except Exception as e:
                print('  FEHLER %s: %s'%(fname,str(e)))
                traceback.print_exc()
    print('  Gesamt: %d Karten'%len(all_cards))
    if not all_cards: raise Exception('Keine Karten geparst - siehe Fehler oben')
    print('\nResolving image paths...')
    img_lookup = {}
    if os.path.isdir(IMAGES_DIR):
        for fname in os.listdir(IMAGES_DIR):
            name, ext = os.path.splitext(fname)
            img_lookup[name.lower()] = fname
        print('  %d images found in images/' % len(img_lookup))
    else:
        print('  WARNING: images/ folder not found, skipping')

    def resolve_pic(pic):
        if not pic: return pic
        name, ext = os.path.splitext(pic)
        if ext:
            # Has extension - just lowercase the whole thing
            return pic.lower()
        # No extension - look up in images folder
        resolved = img_lookup.get(pic.lower())
        return resolved if resolved else pic.lower() + '.jpg'

    fixed = 0
    for c in all_cards:
        orig = c['picture']
        c['picture'] = resolve_pic(c['picture'])
        if c['picture'] != orig: fixed += 1
        for u in c['upgrades']:
            orig_u = u.get('picture', '')
            u['picture'] = resolve_pic(u.get('picture', ''))
            if u['picture'] != orig_u: fixed += 1
    print('  %d picture paths resolved' % fixed)

    print('\nBuilding maps...')
    id_to_name,fusion_from,fusion_to,base_fusion_from,base_fusion_to,summoned_by=build_derived(all_cards,fusion_map)
    print('Schreibe '+OUT_FILE+' ...')
    out={'cards':all_cards,'skill_names':skill_names,'skill_descs':skill_descs,'skill_descs_all':skill_descs_all,'skill_descs_fac':skill_descs_fac,'skill_descs_all_fac':skill_descs_all_fac,'fusion_map':fusion_map,'fusion_from':fusion_from,'fusion_to':fusion_to,'id_to_name':id_to_name,'base_fusion_from':base_fusion_from,'base_fusion_to':base_fusion_to,'summoned_by':summoned_by}
    with open(OUT_FILE,'w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False)
    size_mb=os.path.getsize(OUT_FILE)/1024/1024
    print('\nFertig! %.1f MB - %d Karten'%(size_mb,len(all_cards)))
    success=True
except Exception as e:
    print('\nFEHLER: '+str(e))
    traceback.print_exc()

if success:
    input('\nErfolgreich. Enter zum Beenden...')
else:
    input('\nMit Fehlern beendet. Enter zum Beenden...')
