#!/usr/bin/env python3
"""
Build script for Tyrant Unleashed Card Browser index.html
Run this to regenerate index.html cleanly from scratch.
"""

import re, json, base64, io, os, shutil, subprocess
from PIL import Image

BASE_HTML  = '/home/claude/tyrant_standalone.html'
SKILLSHEET = '/mnt/user-data/uploads/skillicons.png'
RUSH_PNG   = '/mnt/user-data/uploads/TSkillIconRush.png'
ATLAS_PNG  = '/mnt/user-data/uploads/atlas0.png'
BG_JPG     = '/mnt/user-data/uploads/Background.jpg'
OUT_FILE   = '/home/claude/electron_project/src/index.html'

def b64(img, fmt='PNG', quality=None):
    buf = io.BytesIO()
    if quality: img.save(buf, fmt, quality=quality)
    else: img.save(buf, fmt)
    return base64.b64encode(buf.getvalue()).decode()

def extract(img, c, size=32):
    crop = img.crop((c['x'],c['y'],c['x']+c['w'],c['y']+c['h']))
    return crop.resize((size,size), Image.LANCZOS)

print("Loading assets...")
sprite_img = Image.open(SKILLSHEET).convert('RGBA')
rush_img   = Image.open(RUSH_PNG).convert('RGBA')
bg_img     = Image.open(BG_JPG).resize((1366, 768), Image.LANCZOS)

sprite_b64 = 'data:image/png;base64,' + b64(sprite_img)
rush_b64   = 'data:image/png;base64,' + b64(rush_img)
bg_b64     = 'data:image/jpeg;base64,' + b64(bg_img, 'JPEG', quality=70)
print(f"  sprite: {len(sprite_b64)//1024}KB, bg: {len(bg_b64)//1024}KB")

# -- New PNG icons (replace atlas extraction) ----------------------------------
ICONS_DIR = os.path.dirname(os.path.abspath(__file__))
def png_b64(filename):
    path = os.path.join(ICONS_DIR, 'Sprites', filename)
    with open(path, 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

faction_icons = {
    "1": png_b64("filter_align_imperial.png"),
    "2": png_b64("filter_align_raider.png"),
    "3": png_b64("filter_align_bloodthirsty.png"),
    "4": png_b64("filter_align_xeno.png"),
    "5": png_b64("filter_align_righteous.png"),
    "6": png_b64("filter_align_progenitor.png"),
}
rarity_icons = {
    "1": png_b64("filter_rarity_common.png"),
    "2": png_b64("filter_rarity_rare.png"),
    "3": png_b64("filter_rarity_epic.png"),
    "4": png_b64("filter_rarity_legendary.png"),
    "5": png_b64("filter_rarity_vindicator.png"),
    "6": png_b64("filter_rarity_mythic.png"),
}
delay_icons = {
    "0": png_b64("filter_cost_0.png"),
    "1": png_b64("filter_cost_1.png"),
    "2": png_b64("filter_cost_2.png"),
    "3": png_b64("filter_cost_3.png"),
    "4": png_b64("filter_cost_4.png"),
}
fusion_icons = {
    "0": png_b64("filter_fusions_0.png"),
    "1": png_b64("filter_fusions_1.png"),
    "2": png_b64("filter_fusions_2.png"),
}
type_icons = {
    "assault":   png_b64("filter_type_assault.png"),
    "commander": png_b64("filter_type_commander.png"),
    "structure": png_b64("filter_type_structure.png"),
}
print("  PNG icons: faction×6, rarity×6, delay×5, fusion×3, type×3")

# -- Skill sprite map ----------------------------------------------------------
SKILL_SPRITE_MAP = {
  "armored":   {"x":1,  "y":231,"w":35,"h":34}, "pierce":   {"x":182,"y":369,"w":34,"h":35},
  "strike":    {"x":215,"y":333,"w":37,"h":35}, "heal":     {"x":216,"y":405,"w":36,"h":35},
  "rally":     {"x":110,"y":368,"w":34,"h":37}, "evade":    {"x":2,  "y":477,"w":33,"h":33},
  "besiege":   {"x":143,"y":332,"w":38,"h":38}, "counter":  {"x":108,"y":475,"w":36,"h":36},
  "enfeeble":  {"x":217,"y":371,"w":35,"h":33}, "flurry":   {"x":69, "y":367,"w":41,"h":38},
  "protect":   {"x":178,"y":266,"w":37,"h":34}, "summon":   {"x":34, "y":204,"w":35,"h":29},
  "jam":       {"x":181,"y":476,"w":35,"h":34}, "stasis":   {"x":37, "y":367,"w":33,"h":39},
  "absorb":    {"x":69, "y":202,"w":33,"h":33}, "berserk":  {"x":142,"y":476,"w":40,"h":35},
  "swipe":     {"x":0,  "y":405,"w":36,"h":36}, "corrosive":{"x":180,"y":441,"w":37,"h":34},
  "venom":     {"x":109,"y":296,"w":36,"h":39}, "leech":    {"x":37, "y":406,"w":34,"h":34},
  "fortify":   {"x":105,"y":202,"w":34,"h":34}, "inhibit":  {"x":35, "y":476,"w":38,"h":36},
  "hunt":      {"x":105,"y":233,"w":36,"h":32}, "allegiance":{"x":69,"y":234,"w":38,"h":31},
  "avenge":    {"x":0,  "y":366,"w":36,"h":40}, "scavenge": {"x":35, "y":262,"w":37,"h":36},
  "enrage":    {"x":217,"y":475,"w":37,"h":37}, "enhance":  {"x":108,"y":332,"w":34,"h":35},
  "refresh":   {"x":144,"y":265,"w":34,"h":33}, "legion":   {"x":70, "y":440,"w":39,"h":37},
  "barrier":   {"x":137,"y":206,"w":34,"h":30}, "wall":     {"x":216,"y":299,"w":36,"h":34},
  "entrap":    {"x":0,  "y":328,"w":37,"h":43}, "sunder":   {"x":143,"y":231,"w":37,"h":33},
  "mimic":     {"x":217,"y":265,"w":35,"h":34}, "subdue":   {"x":33, "y":182,"w":37,"h":25},
  "overload":  {"x":144,"y":366,"w":37,"h":38}, "payback":  {"x":71, "y":297,"w":39,"h":36},
  "valor":     {"x":180,"y":229,"w":35,"h":36}, "coalition":{"x":69, "y":261,"w":38,"h":38},
  "evolve":    {"x":215,"y":232,"w":37,"h":33}, "bravery":  {"x":0,  "y":200,"w":33,"h":33},
  "revenge":   {"x":106,"y":438,"w":39,"h":39}, "drain":    {"x":109,"y":402,"w":36,"h":37},
  "disease":   {"x":36, "y":229,"w":35,"h":34}, "poison":   {"x":35, "y":296,"w":37,"h":36},
  "mark":      {"x":0,  "y":173,"w":29,"h":30}, "sabotage": {"x":179,"y":331,"w":37,"h":39},
  "siege":     {"x":142,"y":297,"w":38,"h":38}, "mend":     {"x":70, "y":475,"w":40,"h":37},
  "tribute":   {"x":177,"y":298,"w":40,"h":37}, "flying":   {"x":0,  "y":437,"w":36,"h":40},
}
SKILL_ROTATION = {
  "armored":"270","summon":"270","venom":"270","allegiance":"270",
  "barrier":"270","wall":"270","subdue":"270","payback":"270",
  "evolve":"90","poison":"270",
}
print(f"  Skill sprite map: {len(SKILL_SPRITE_MAP)} skills + new standalone skill PNGs")

# -- Build icon constants JS block ---------------------------------------------
ICONS_JS = f"""
const FACTION_ICONS = {json.dumps(faction_icons)};
const RARITY_ICONS  = {json.dumps(rarity_icons)};
const DELAY_ICONS   = {json.dumps(delay_icons)};
const FUSION_ICONS  = {json.dumps(fusion_icons)};
const TYPE_ICONS    = {json.dumps(type_icons)};
const FAC_NAMES = {{"1":"Imperial","2":"Raider","3":"Bloodthirsty","4":"Xeno","5":"Righteous","6":"Progenitor"}};
const RARITY_NAMES  = {{"1":"Common","2":"Rare","3":"Epic","4":"Legendary","5":"Vindicator","6":"Mythic"}};

const SKILL_ICONS_B64  = 'data:image/png;base64,{sprite_b64[22:]}';
const SKILL_SPRITE_MAP = {json.dumps(SKILL_SPRITE_MAP)};
const SKILL_ROTATION   = {json.dumps(SKILL_ROTATION)};
const SKILL_STANDALONE = {{"rush":"{rush_b64}","armored":"'+ png_b64(\"armored32.png\") +'","avenge":"'+ png_b64(\"avenge32.png\") +'","berserk":"'+ png_b64(\"berserk32.png\") +'","besiege":"'+ png_b64(\"besiege32.png\") +'","coalition":"'+ png_b64(\"coalition32.png\") +'","corrosive":"'+ png_b64(\"corrosive32.png\") +'","counter":"'+ png_b64(\"counter32.png\") +'","drain":"'+ png_b64(\"drain32.png\") +'","enfeeble":"'+ png_b64(\"enfeeble32.png\") +'","enhance":"'+ png_b64(\"enhance32.png\") +'","enrage":"'+ png_b64(\"enrage32.png\") +'","entrap":"'+ png_b64(\"entrap32.png\") +'","evade":"'+ png_b64(\"evade32.png\") +'","evolve":"'+ png_b64(\"evolve32.png\") +'","flurry":"'+ png_b64(\"flurry32.png\") +'","flying":"'+ png_b64(\"flying32.png\") +'","heal":"'+ png_b64(\"heal32.png\") +'","inhibit":"'+ png_b64(\"inhibit32.png\") +'","jam":"'+ png_b64(\"jam32.png\") +'","leech":"'+ png_b64(\"leech32.png\") +'","legion":"'+ png_b64(\"legion32.png\") +'","mend":"'+ png_b64(\"mend32.png\") +'","overload":"'+ png_b64(\"overload32.png\") +'","payback":"'+ png_b64(\"payback32.png\") +'","pierce":"'+ png_b64(\"pierce32.png\") +'","poison":"'+ png_b64(\"poison32.png\") +'","protect":"'+ png_b64(\"protect32.png\") +'","rally":"'+ png_b64(\"rally32.png\") +'","refresh":"'+ png_b64(\"refresh32.png\") +'","revenge":"'+ png_b64(\"revenge32.png\") +'","sabotage":"'+ png_b64(\"sabotage32.png\") +'","stasis":"'+ png_b64(\"stasis32.png\") +'","strike":"'+ png_b64(\"strike32.png\") +'","sunder":"'+ png_b64(\"sunder32.png\") +'","swipe":"'+ png_b64(\"swipe32.png\") +'","tribute":"'+ png_b64(\"tribute32.png\") +'","valor":"'+ png_b64(\"valor32.png\") +'","venom":"'+ png_b64(\"venom32.png\") +'","wall":"'+ png_b64(\"wall32.png\") +'","weaken":"'+ png_b64(\"weaken32.png\") +'"}};

const _skillIconCache = {{}};
let _spriteLoaded = false;
const _spriteImgEl = new Image();
_spriteImgEl.onload = function() {{
  _spriteLoaded = true;
  Object.keys(SKILL_SPRITE_MAP).forEach(sk => _renderSkillIcon(sk));
  document.querySelectorAll('.fsb[data-sk]').forEach(btn => {{
    const sk = btn.dataset.sk, ic = _skillIconCache[sk];
    if(ic) {{ const img=btn.querySelector('img.sk-spr'); if(img){{img.src=ic;img.style.opacity='1';}} }}
  }});
}};
_spriteImgEl.src = SKILL_ICONS_B64;

function _renderSkillIcon(skillId) {{
  if(_skillIconCache[skillId]) return _skillIconCache[skillId];
  if(SKILL_STANDALONE[skillId]) {{ _skillIconCache[skillId]=SKILL_STANDALONE[skillId]; return SKILL_STANDALONE[skillId]; }}
  if(!_spriteLoaded) return null;
  const m=SKILL_SPRITE_MAP[skillId]; if(!m) return null;
  const SIZE=24, cv=document.createElement('canvas');
  cv.width=SIZE; cv.height=SIZE;
  const ctx=cv.getContext('2d'); ctx.imageSmoothingEnabled=false;
  const rot=SKILL_ROTATION[skillId]||'0';
  ctx.save(); ctx.translate(SIZE/2,SIZE/2);
  if(rot.includes('270')) ctx.rotate(-Math.PI/2);
  else if(rot.includes('90')) ctx.rotate(Math.PI/2);
  else if(rot.includes('180')) ctx.rotate(Math.PI);
  if(rot.includes('flipH')) ctx.scale(-1,1);
  ctx.drawImage(_spriteImgEl,m.x,m.y,m.w,m.h,-SIZE/2,-SIZE/2,SIZE,SIZE);
  ctx.restore();
  const dataUrl=cv.toDataURL(); _skillIconCache[skillId]=dataUrl; return dataUrl;
}}
"""

# -- Sort buttons JS -----------------------------------------------------------
SORT_JS = """
// -- Dynamic grid layout -----------------------------------------------------
const TILE_MIN_W = 160, TILE_GAP = 7, FOOT_H = 48;

function calcGrid() {
  const ga = document.getElementById('grid-area');
  // Use clientWidth if available, fall back to window width minus scrollbar
  const gw = Math.max(ga.clientWidth, window.innerWidth) - 24;
  const gh = Math.max(ga.clientHeight, window.innerHeight - 50) - FOOT_H - 20;
  if (gw < 100) { requestAnimationFrame(calcGrid); return; } // not laid out yet
  const cols = Math.max(3, Math.floor((gw + TILE_GAP) / (TILE_MIN_W + TILE_GAP)));
  const tileW = Math.floor((gw - (cols-1)*TILE_GAP) / cols);
  const tileH = Math.round(tileW / 1.05) + 40;
  const rows  = Math.max(1, Math.floor((gh + TILE_GAP) / (tileH + TILE_GAP)));
  document.documentElement.style.setProperty('--grid-cols', cols);
  const newPage = cols * rows;
  if (newPage !== PAGE) {
    PAGE = newPage; page = 0;
    if(typeof filtered !== 'undefined' && filtered.length) { renderGrid(); renderPg(); }
  }
}

// ResizeObserver for accurate resize detection
if(window.ResizeObserver) {
  let _ro = new ResizeObserver(() => calcGrid());
  document.addEventListener('DOMContentLoaded', () => {
    const ga = document.getElementById('grid-area');
    if(ga) _ro.observe(ga);
  });
} else {
  let _rt;
  window.addEventListener('resize', () => { clearTimeout(_rt); _rt = setTimeout(calcGrid, 80); });
}

let sortKey='name', sortAsc=true;
function setSort(key){
  if(sortKey===key){ sortAsc=!sortAsc; } else { sortKey=key; sortAsc=(key==='name'); }
  document.querySelectorAll('.sort-btn').forEach(b=>{
    const on=b.dataset.sort===sortKey;
    b.classList.toggle('active',on);
    b.querySelector('.sort-arrow').textContent=on?(sortAsc?'↑':'↓'):'';
  });
  applyF();
}
"""

# -- Load function -------------------------------------------------------------
LOAD_JS = """
function load(){
  const bar=document.getElementById('load-bar');
  const msg=document.getElementById('load-msg');
  msg.textContent='Loading card database...'; bar.style.width='10%';
  if(window.electronAPI&&window.electronAPI.onUpdateStatus){
    window.electronAPI.onUpdateStatus(function(s){
      const el=document.getElementById('update-status'); if(!el) return;
      if(s.state==='checking')       {el.style.color='#3a6688';el.textContent='🔍 Prüfe Kartendaten...';}
      else if(s.state==='up-to-date'){el.style.color='#2a6644';el.textContent='✓ Aktuell';setTimeout(()=>el.textContent='',3000);}
      else if(s.state==='downloading'){el.style.color='#aa8822';el.textContent=`⬇ ${s.count} XML(s)...`;}
      else if(s.state==='progress')  {el.style.color='#aa8822';el.textContent=`⬇ ${s.pct}% – ${s.file||''}`;}
      else if(s.state==='done')      {el.style.color='#2a9955';el.textContent=`✓ ${s.cards} Karten (${s.version})`;setTimeout(()=>el.textContent='',5000);}
      else if(s.state==='offline')   {el.style.color='#3a5577';el.textContent='📴 Offline';setTimeout(()=>el.textContent='',4000);}
    });
  }
  if(window.electronAPI&&window.electronAPI.loadData){
    window.electronAPI.loadData((progress,rawJson)=>{
      if(rawJson===null){ bar.style.width=progress+'%'; msg.textContent='Reading... '+progress+'%'; }
      else {
        bar.style.width='85%'; msg.textContent='Parsing cards...';
        setTimeout(()=>{
          try{
            const d=JSON.parse(rawJson);
            cards=d.cards; skNames=d.skill_names; skDescs=d.skill_descs; skDescsAll=d.skill_descs_all||{}; skDescsFac=d.skill_descs_fac||{}; skDescsAllFac=d.skill_descs_all_fac||{}; fusMap=d.fusion_map; fusFrom=d.fusion_from||{}; fusTo=d.fusion_to||{}; idToName=d.id_to_name||{}; baseFusFrom=d.base_fusion_from||{}; baseFusTo=d.base_fusion_to||{};
            bar.style.width='100%'; msg.textContent='Done!';
            setTimeout(init,100);
          } catch(e){
            document.getElementById('load-msg').style.color='#ff4444';
            document.getElementById('load-msg').textContent='Parse error: '+e.message;
          }
        },50);
      }
    });
  } else {
    msg.style.color='#ff4444'; msg.textContent='Error: not running in Electron';
  }
}
"""

print("\nLoading base HTML...")
with open(BASE_HTML, 'r', encoding='utf-8') as f:
    html = f.read()

print("Applying transforms...")

# 1. Background
html = html.replace(
    'body{height:100%;background:#161c24;',
    f"body{{height:100%;background:#161c24 url('data:image/jpeg;base64,{bg_b64}') center/cover no-repeat fixed;"
)
print("  ✓ Background")

# 2. Topbar glass + sort buttons CSS
html = html.replace(
    'background:linear-gradient(180deg,#1a2c3e 0%,#0f1c2a 100%)',
    'background:linear-gradient(180deg,rgba(15,28,42,0.92) 0%,rgba(10,18,25,0.92) 100%)'
)
sort_css = """.sort-btn{padding:5px 9px;background:rgba(255,255,255,.05);border:1px solid #1a3040;
  color:#5577aa;font-size:11px;font-weight:700;cursor:pointer;border-radius:3px;
  letter-spacing:.3px;white-space:nowrap;display:flex;align-items:center;gap:3px}
.sort-btn:hover{border-color:#3a6088;color:#99bbcc}
.sort-btn.active{border-color:#00ccff88;color:#00ccff;background:rgba(0,180,255,.08)}
.sort-btn .sort-arrow{font-size:9px;opacity:.7}
#sort-wrap{display:flex;gap:4px;align-items:center;margin-right:6px}
"""
html = html.replace('/* ── TOPBAR', sort_css + '/* ── TOPBAR', 1)
print("  ✓ Sort CSS + topbar glass")

# 3. Fix RAR names
html = re.sub(
    r"const RAR = \{[^}]+\};",
    "const RAR = {'1':{name:'Common',c:'#99aabc'},'2':{name:'Rare',c:'#44bb66'},'3':{name:'Epic',c:'#4488ff'},'4':{name:'Legendary',c:'#bb44ff'},'5':{name:'Vindicator',c:'#ffaa22'},'6':{name:'Mythic',c:'#ff2266'}};",
    html
)
print("  ✓ RAR names")

# 4. Remove rupture
html = re.sub(r"\s+rupture:\s+`[^`]+`,\n", '\n', html)
html = re.sub(r"\s*rupture:'#[0-9a-fA-F]+',?", '', html)
print("  ✓ Rupture removed")

# 5. Fix imgSrc to use tu-img://
old_imgsrc_re = re.search(r'function imgSrc\(pic\)\{[^}]+\}', html, re.DOTALL)
if old_imgsrc_re:
    html = html[:old_imgsrc_re.start()] + """function imgSrc(pic){
  if(!pic) return '';
  if(window.electronAPI&&window.electronAPI.imageBase) return window.electronAPI.imageBase+pic;
  const b=document.getElementById('imgpath-input')?.value?.trim()||'';
  if(!b) return pic;
  return b.endsWith('/')||b.endsWith('\\\\')?b+pic:b+'/'+pic;
}""" + html[old_imgsrc_re.end():]
    print("  ✓ imgSrc → tu-img://")

# 6. Inject ICONS_JS at top of <script>
script_pos = html.rfind('<script>') + len('<script>')
html = html[:script_pos] + ICONS_JS + html[script_pos:]
print("  ✓ Icon constants injected")

# 7. Replace TU_DATA loading with IPC load()
# Remove TU_DATA using brace-counting (precise)
tu_start = html.find('\nconst TU_DATA=')
if tu_start != -1:
    depth = 0; i = tu_start + len('\nconst TU_DATA=')
    tu_obj_end = None
    while i < len(html):
        if html[i] == '{': depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0: tu_obj_end = i + 1; break
        i += 1
    # tu_obj_end points after closing }, followed by ';\nfunction load(){'
    # Remove: from tu_start to tu_obj_end+1 (skip the semicolon too)
    after_tu = html[tu_obj_end:]  # starts with ';\nfunction load()...'
    # Find end of standalone load() using brace counting
    load_fn_start = after_tu.find('function load(){')
    depth = 0; i = load_fn_start
    load_fn_end = None
    while i < len(after_tu):
        if after_tu[i] == '{': depth += 1
        elif after_tu[i] == '}':
            depth -= 1
            if depth == 0: load_fn_end = i + 1; break
        i += 1
    # Replace: TU_DATA + semicolon + standalone load() → our IPC load()
    removal_end = tu_obj_end + 1 + load_fn_end  # +1 for semicolon
    html = html[:tu_start] + '\n' + LOAD_JS + html[removal_end:]
    print("  ✓ TU_DATA removed + load() replaced (precise)")
else:
    print("  ✗ TU_DATA not found")


# 8. Add sort state + setSort() before applyF
html = html.replace('function applyF(){', SORT_JS + 'function applyF(){', 1)
print("  ✓ Sort logic injected")

# 9. Fix applyF sort to be dynamic
html = html.replace(
    "filtered.sort((a,b)=>a.name.localeCompare(b.name));",
    """filtered.sort((a,b)=>{
    if(sortKey==='name')     {const r=( a.name||'').localeCompare(b.name||''); return sortAsc?r:-r;}
    if(sortKey==='id')       {const va=parseInt(a.id)||0,vb=parseInt(b.id)||0; return sortAsc?va-vb:vb-va;}
    if(sortKey==='type')     {const r=( a.type||'').localeCompare(b.type||''); return sortAsc?r:-r;}
    if(sortKey==='unit_type'){const r=(a.unit_type||'').localeCompare(b.unit_type||''); return sortAsc?r:-r;}
    const vals={rarity:[parseInt(a.rarity)||0,parseInt(b.rarity)||0],
                delay:[parseInt(maxD(a).cost)||0,parseInt(maxD(b).cost)||0],
                fusion:[parseInt(a.fusion_level)||0,parseInt(b.fusion_level)||0]};
    const [va,vb]=vals[sortKey]||[0,0]; return sortAsc?va-vb:vb-va;
  });"""
)
print("  ✓ Dynamic sort")

# 10. Add sort buttons to topbar HTML
html = html.replace(
    '    <div id="topbar-logo">TU</div>\n    <div id="topbar-count">',
    '    <div id="topbar-logo">TU</div>\n    <div id="topbar-count">'
)
sort_buttons = '''    <div id="sort-wrap">
      <div class="sort-btn active" data-sort="name"     onclick="setSort('name')"    >Name    <span class="sort-arrow">↑</span></div>
      <div class="sort-btn"        data-sort="type"     onclick="setSort('type')"    >Faction <span class="sort-arrow"></span></div>
      <div class="sort-btn"        data-sort="rarity"   onclick="setSort('rarity')"  >Rarity  <span class="sort-arrow"></span></div>
      <div class="sort-btn"        data-sort="delay"    onclick="setSort('delay')"   >Cost    <span class="sort-arrow"></span></div>
      <div class="sort-btn"        data-sort="fusion"   onclick="setSort('fusion')"  >Fusion  <span class="sort-arrow"></span></div>
      <div class="sort-btn"        data-sort="unit_type" onclick="setSort('unit_type')">Type  <span class="sort-arrow"></span></div>
    </div>
    <input id="imgpath-input" type="hidden" value="" />'''
# Find filter button and insert sort before it
html = html.replace(
    '    <button id="filter-btn">',
    sort_buttons + '\n    <button id="filter-btn">'
)
# Remove old imgpath input if it exists
html = html.replace('\n    <input id="imgpath-input" type="text" placeholder="e.g. C:/TU/images/  or  ./images/" />', '')
html = html.replace('\n    <div id="imgpath-lbl">🖼 Images:</div>', '')
print("  ✓ Sort buttons added to topbar")

# 11. Replace filter buttons with atlas icons
def make_fib_atlas(data_attr, val, icon_b64, title, border_color):
    return (f'<div class="fib" data-{data_attr}="{val}" title="{title}" '
            f'style="border-color:{border_color}">'
            f'<img src="{icon_b64}" style="width:28px;height:28px;'
            f'object-fit:contain;image-rendering:pixelated"></div>')

# Rarity
rar_colors = {"1":"#99aabc44","2":"#44bb6644","3":"#4488ff44","4":"#bb44ff44","5":"#ffaa2244","6":"#ff226644"}
rar_names  = {"1":"Common","2":"Rare","3":"Epic","4":"Legendary","5":"Vindicator","6":"Mythic"}
new_rar = '\n        '.join([make_fib_atlas('rar',i,rarity_icons[i],rar_names[i],rar_colors[i]) for i in ["1","2","3","4","5","6"]])
old_rar = re.search(r'<div class="fib" data-rar="1">.*?</div>\s*<div class="fib" data-rar="6">.*?</div>', html, re.DOTALL)
if old_rar: html = html[:old_rar.start()] + new_rar + html[old_rar.end():]

# Faction
fac_colors = {"1":"#00ccff44","2":"#ff992244","3":"#ff333344","4":"#00ee7744","5":"#ffcc2244","6":"#cc44ff44"}
fac_names  = {"1":"Imperial","2":"Raider","3":"Bloodthirsty","4":"Xeno","5":"Righteous","6":"Progenitor"}
for fid in ["1","2","3","4","5","6"]:
    old = re.search(rf'<div class="fib" data-fac="{fid}"[^>]*>.*?</div>', html, re.DOTALL)
    if old: html = html[:old.start()] + make_fib_atlas('fac',fid,faction_icons[fid],fac_names[fid],fac_colors[fid]) + html[old.end():]

# Delay
new_del = '\n        '.join([make_fib_atlas('del',i,delay_icons[i],f'Delay {i}','#00ccff22') for i in ["0","1","2","3","4"]])
old_del = re.search(r'<div class="fib" data-del="0">.*?</div>\s*<div class="fib" data-del="4">.*?</div>', html, re.DOTALL)
if old_del: html = html[:old_del.start()] + new_del + html[old_del.end():]

# Fusion
new_fus = '\n        '.join([make_fib_atlas('fus',i,fusion_icons[i],f'Fusion {i}','#cc44ff22') for i in ["0","1","2"]])
old_fus = re.search(r'(<div[^>]*id="fd-fus"[^>]*>)(.*?)(</div>\s*<!--)', html, re.DOTALL)
if old_fus: html = html[:old_fus.start(1)+len(old_fus.group(1))] + '\n        ' + new_fus + '\n      ' + html[old_fus.start(3):]

# Type
for k in ["assault","commander","structure"]:
    old = re.search(rf'<div class="fib type-ic" data-ut="{k}"[^>]*>.*?</div>', html, re.DOTALL)
    if old: html = html[:old.start()] + make_fib_atlas('ut',k,type_icons[k],k.capitalize(),'#44dd6622') + html[old.end():]

print("  ✓ All atlas icons replaced in filter")

# Fix rarity filter button icons directly in HTML (buttons are hardcoded, not loaded from RARITY_ICONS)
import re as _re2
rar_map = {
    '1': ('Common',    '#99aabc44', rarity_icons['1']),
    '2': ('Rare',      '#44bb6644', rarity_icons['2']),
    '3': ('Epic',      '#4488ff44', rarity_icons['3']),
    '4': ('Legendary', '#bb44ff44', rarity_icons['4']),
    '5': ('Vindicator','#ffaa2244', rarity_icons['5']),
    '6': ('Mythic',    '#ff226644', rarity_icons['6']),
}
for rar, (title, color, icon) in rar_map.items():
    pattern = r'(<div class="fib" data-rar="' + rar + r'" title="' + title + r'"[^>]*>)<img src="data:image/png;base64,[^"]*"'
    replacement = r'\1<img src="' + icon + '"'
    html = _re2.sub(pattern, replacement, html)
print("  ✓ Rarity filter button icons corrected (direct replacement)")

# 12. Update buildSkillGrid to use sprites
html = html.replace(
    '''function buildSkillGrid(){
  const skList=Object.keys(SPATH).sort();
  document.getElementById('fd-sk-grid').innerHTML=skList.map(sk=>{
    const c=SCOL[sk]||'#aabbcc';
    const nm=skNames[sk]||sk;
    return `<div class="fsb" data-sk="${sk}">
      <svg viewBox="0 0 32 32" style="fill:${c};color:${c}">${SPATH[sk]}</svg>
      <div class="fsb-tt">${nm}</div>
    </div>`;
  }).join('');''',
    '''function buildSkillGrid(){
  const allSk=[...new Set([...Object.keys(SPATH),...Object.keys(SKILL_STANDALONE)])].sort();
  document.getElementById('fd-sk-grid').innerHTML=allSk.map(sk=>{
    const c=SCOL[sk]||'#aabbcc', nm=skNames[sk]||sk;
    const cached=_skillIconCache[sk];
    const icoHtml=cached
      ?`<img class="sk-spr" src="${cached}" style="width:21px;height:21px;image-rendering:pixelated;display:block;margin:0 auto">`
      :(SKILL_SPRITE_MAP[sk]||SKILL_STANDALONE[sk])
        ?`<img class="sk-spr" src="" style="width:21px;height:21px;display:block;margin:0 auto;opacity:0">`
        :`<svg viewBox="0 0 32 32" style="fill:${c};color:${c}">${SPATH[sk]||''}</svg>`;
    return `<div class="fsb" data-sk="${sk}">${icoHtml}<div class="fsb-tt">${nm}</div></div>`;
  }).join('');
  allSk.forEach(sk=>{const ic=_renderSkillIcon(sk);if(ic){const img=document.querySelector(`.fsb[data-sk="${sk}"] img.sk-spr`);if(img){img.src=ic;img.style.opacity='1';}}});'''
)
print("  ✓ buildSkillGrid → sprites")

# 13. Update renderDet skill icons to use sprites
html = html.replace(
    '          <svg viewBox="0 0 32 32" style="fill:${col};color:${col}">${path}</svg>',
    '          ${_renderSkillIcon(sk.id)?`<img src="${_renderSkillIcon(sk.id)}" style="width:13px;height:13px;image-rendering:pixelated">`:(`<svg viewBox="0 0 32 32" style="fill:${col};color:${col}">${SPATH[sk.id]||\'\'}</svg>`)}'
)
# Remove path variable if it's now unused
html = html.replace(
    "      const path=SPATH[sk.id]||'<circle cx=\"16\" cy=\"16\" r=\"8\"/>';\n",
    ''
)
print("  ✓ renderDet skill icons → sprites")

# 14. Fix matches() type coercion
html = html.replace(
    'if(fa.rar.size&&!fa.rar.has(c.rarity))',
    'if(fa.rar.size&&!fa.rar.has(String(c.rarity)))'
)
html = html.replace(
    "if(fa.fus.size&&!fa.fus.has(c.fusion_level||'0'))",
    "if(fa.fus.size&&!fa.fus.has(String(c.fusion_level||0)))"
)
print("  ✓ matches() type coercion")

# 15. Fix faction_id → type
html = html.replace('d.faction_id','d.type').replace('c.faction_id','c.type')
print("  ✓ faction_id → type")



# 16b. Fix matches() to include delay filter using 'cost' field
old_matches_del = "  if(fa.fac.size && !fa.fac.has(c.type)) return false;\n  if(fa.fus.size"
new_matches_del = "  if(fa.fac.size && !fa.fac.has(c.type)) return false;\n  if(fa.del.size && !fa.del.has(String(maxD(c).cost||0))) return false;\n  if(fa.fus.size"
if old_matches_del in html:
    html = html.replace(old_matches_del, new_matches_del)
    print("  ✓ matches() delay filter added (uses cost field)")
else:
    print("  ✗ matches() delay pattern not found")

# 12b. Rebuild filter layout in correct order
def extract_grp(html, grp_id):
    start = html.find(f'id="{grp_id}"')
    inner_start = html.find('>', start) + 1
    depth = 0; i = inner_start
    while i < len(html):
        if html[i:i+4] == '<div': depth += 1
        elif html[i:i+6] == '</div>':
            if depth == 0: return html[inner_start:i].strip()
            depth -= 1
        i += 1
    return ''

rar_btns = extract_grp(html, 'fd-rar')
fac_btns = extract_grp(html, 'fd-fac')
del_btns = extract_grp(html, 'fd-delay')
fus_btns = extract_grp(html, 'fd-fus')
ut_btns  = extract_grp(html, 'fd-utype')

new_filter_rows = f"""
    <!-- Rarity -->
    <div class="fd-row">
      <div class="fd-lbl">Rarity</div>
      <div class="fd-grp" id="fd-rar">
        {rar_btns}
      </div>
    </div>
    <!-- Faction -->
    <div class="fd-row">
      <div class="fd-lbl">Faction</div>
      <div class="fd-grp fic" id="fd-fac">
        {fac_btns}
      </div>
    </div>
    <!-- Delay + Fusion -->
    <div class="fd-row">
      <div class="fd-lbl">Cost</div>
      <div class="fd-grp" id="fd-delay">
        {del_btns}
      </div>
      <div class="fd-lbl" style="margin-left:12px">Fusion</div>
      <div class="fd-grp" id="fd-fus">
        {fus_btns}
      </div>
    </div>
    <!-- Type -->
    <div class="fd-row">
      <div class="fd-lbl">Type</div>
      <div class="fd-grp" id="fd-utype">
        {ut_btns}
      </div>
    </div>
    <!-- Skills -->
    <div class="fd-sk-hdr">
      <span class="fd-sk-lbl">Skill</span>
    </div>
    <div class="fd-sk-grid" id="fd-sk-grid"></div>
"""

# Find and replace the filter rows section
row_start = html.find('<!-- Rarity -->')
foot_start = html.find('    <div class="fd-foot">')
if row_start != -1 and foot_start != -1:
    html = html[:row_start] + new_filter_rows + '\n' + html[foot_start:]
    print("  ✓ Filter layout rebuilt (correct order)")
else:
    print(f"  ✗ Filter rebuild failed: row_start={row_start}, foot={foot_start}")


# 16c. Fix skill label rendering (s attr, y=faction, all 4 desc variants)
OLD_SKLBL = (
    "      let lbl=dispName;\n"
    "      if(sk.all==='1') lbl+=' All';\n"
    "      if(sk.x) lbl+=' '+sk.x;\n"
    "      if(sk.y) lbl+='/'+sk.y;\n"
    "      if(sk.trigger) lbl+=' ['+sk.trigger+']';\n"
    "      const desc=skDescs[sk.id]||'';"
)
NEW_SKLBL = (
    "      let lbl=dispName;\n"
    "      if(sk.all==='1') lbl+=' All';\n"
    "      if(sk.s) lbl+=' '+(skNames[sk.s]||sk.s);\n"
    "      if(sk.s2) lbl+=' → '+(skNames[sk.s2]||sk.s2);\n"
    "      if(sk.y && sk.y!=='0') lbl+=' '+(FAC_NAMES[sk.y]||sk.y);\n"
    "      if(sk.x) lbl+=' '+sk.x;\n"
    "      if(sk.n && sk.n!=='1') lbl+=' ('+sk.n+' targets)';\n"
    "      if(sk.c) lbl+=' every '+sk.c;\n"
    "      if(sk.trigger) lbl+=' ['+sk.trigger+']';\n"
    "      const _hasFac=sk.y&&sk.y!=='0', _isAll=sk.all==='1';\n"
    "      let desc='';\n"
    "      if(_isAll&&_hasFac&&skDescsAllFac[sk.id]) desc=skDescsAllFac[sk.id].replace('y ',FAC_NAMES[sk.y]+' ');\n"
    "      else if(_isAll&&skDescsAll[sk.id])        desc=skDescsAll[sk.id];\n"
    "      else if(_hasFac&&skDescsFac[sk.id])       desc=skDescsFac[sk.id].replace('y ',FAC_NAMES[sk.y]+' ');\n"
    "      else                                       desc=skDescs[sk.id]||'';"
)
if OLD_SKLBL in html:
    html = html.replace(OLD_SKLBL, NEW_SKLBL)
    print("  ✓ Skill label + desc selection updated (all 4 variants)")
else:
    print("  ✗ Skill label pattern not found")


# Responsive grid: no scroll, dynamic cols/rows
html = html.replace(
    '#card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(124px,1fr))',
    '#card-grid{display:grid;grid-template-columns:repeat(var(--grid-cols,8),1fr)'
)
html = html.replace(
    '#grid-scroller{flex:1;overflow-y:auto;padding:10px 12px}',
    '#grid-scroller{flex:1;overflow:hidden;padding:10px 12px;display:flex;flex-direction:column}'
)
html = html.replace('const PAGE = 60;', 'let PAGE = 60;')
print("  ✓ Responsive grid CSS + PAGE let")

# Cap grid rows at 5 (better for large/4K displays)
html = html.replace(
    '  const cols = Math.max(3, Math.floor((gw + TILE_GAP) / (TILE_MIN_W + TILE_GAP)));',
    '  const cols = Math.min(13, Math.max(3, Math.floor((gw + TILE_GAP) / (TILE_MIN_W + TILE_GAP))));'
)
html = html.replace(
    '  const rows  = Math.max(1, Math.floor((gh + TILE_GAP) / (tileH + TILE_GAP)));',
    '  const rows  = Math.min(5, Math.max(1, Math.floor((gh + TILE_GAP) / (tileH + TILE_GAP))));'
)
print("  ✓ Grid capped at 13 cols × 5 rows")


# Info table: add fusFrom/fusTo vars + CSS + renderDet info panel
# Step A: add variable declarations
html = html.replace(
    "let fusFrom={}, fusTo={}, idToName={}, baseFusFrom={}, baseFusTo={};\nlet fa={",
    "let fa={"
) if "let fusFrom={}, fusTo={}, idToName={}, baseFusFrom={}, baseFusTo={};" in html else html  # remove if already added

html = html.replace("let fa={", "let fusFrom={}, fusTo={}, idToName={}, baseFusFrom={}, baseFusTo={};\nlet fa={", 1)

# Step B: CSS for info table
infotable_css = """
.ic{width:auto;max-width:600px;display:flex;gap:0;flex-direction:row;position:relative}
.ic-card-col{width:245px;flex-shrink:0;position:relative}
.ic-infotable{flex:1;background:#060e18;border-left:1px solid #1a3040;
  border-radius:0 9px 9px 0;overflow-y:auto;padding:10px 14px;min-width:200px}
.ic-irow{display:flex;gap:8px;padding:5px 0;border-bottom:1px solid #0d1c28;font-size:13px;line-height:1.4}
.ic-irow:last-child{border-bottom:none}
.ic-ilbl{color:#3a6088;font-weight:700;min-width:100px;flex-shrink:0}
.ic-ival{color:#aabbcc;word-break:break-word}
.ic-ival-sm{font-size:9px;color:#2a5070;font-family:monospace}
"""
# Insert before existing .ic{ 
html = html.replace(".ic{width:245px;", infotable_css + ".ic-inner-wrap{width:245px;")
# Wrap the ic-inner content
print("  ✓ Info table CSS added")

# Step C: Inject fusFrom/fusTo loading in load()
old_fus = "fusMap=d.fusion_map;"
new_fus = "fusMap=d.fusion_map; fusFrom=d.fusion_from||{}; fusTo=d.fusion_to||{}; idToName=d.id_to_name||{}; baseFusFrom=d.base_fusion_from||{}; baseFusTo=d.base_fusion_to||{};"
if old_fus in html:
    html = html.replace(old_fus, new_fus)
    print("  ✓ fusFrom/fusTo loaded")

# Step D: Inject info table into renderDet innerHTML
old_art_end = "    <div class=\"ic-skills\">${skHtml}</div>\n    ${fusHtml}"
new_art_end  = "    <div class=\"ic-skills\">${skHtml}</div>\n    ${fusHtml}"  # same for now

# Inject infoHtml computation + HTML into det-inner template
old_det_start = "  const d=lvlD(c,li);\n  const f=FAC[c.type]||FAC['0'];\n  const lvls=[c,...(c.upgrades||[])];\n  const setName=SETS[c.set]||('Set '+c.set);\n  const hpMax=parseInt(maxD(c).health)||0;"

new_det_start = r"""  const d=lvlD(c,li);
  const f=FAC[c.type]||FAC['0'];
  const lvls=[c,...(c.upgrades||[])];
  const setName=SETS[c.set]||('Set '+c.set);
  const hpMax=parseInt(maxD(c).health)||0;
  // Info table data
  const _cid=String(c.id);
  const _fromNames=baseFusFrom[_cid]||[];
  const _toNames=baseFusTo[_cid]||[];
  const _fromStr=_fromNames.length?_fromNames.join(' + '):'–';
  const _toStr=_toNames.length?_toNames.join('<br>'):'–';
  const infoHtml=`<div class="ic-infotable">
    <div class="ic-irow"><span class="ic-ilbl">Name</span><span class="ic-ival">${c.name}</span></div>
    <div class="ic-irow"><span class="ic-ilbl">ID</span><span class="ic-ival">${c.id}</span></div>
    <div class="ic-irow"><span class="ic-ilbl">Faction</span><span class="ic-ival">${f.name||'–'}</span></div>
    <div class="ic-irow"><span class="ic-ilbl">Rarity</span><span class="ic-ival">${RAR[String(c.rarity)]?.name||c.rarity}</span></div>
    <div class="ic-irow"><span class="ic-ilbl">Cost</span><span class="ic-ival">${maxD(c).cost||0}</span></div>
    <div class="ic-irow"><span class="ic-ilbl">Picture</span><span class="ic-ival">${d.picture||'–'}</span></div>
    <div class="ic-irow"><span class="ic-ilbl">Asset Bundle</span><span class="ic-ival">${c.asset_bundle||'–'}</span></div>
    <div class="ic-irow"><span class="ic-ilbl">Fusion from</span><span class="ic-ival">${_fromStr}</span></div>
    <div class="ic-irow"><span class="ic-ilbl">Fusion to</span><span class="ic-ival">${_toStr}</span></div>
  </div>`;"""

if old_det_start in html:
    html = html.replace(old_det_start, new_det_start)
    print("  ✓ infoHtml computed in renderDet")
else:
    print("  ✗ renderDet start not found")

# Append infoHtml to the det-inner innerHTML template
old_inner_end = "    <div class=\"ic-bot\">"
new_inner_end  = "    ${infoHtml}\n    <div class=\"ic-bot\">"  # won't work inside ic structure

# Better: inject infoHtml after the closing backtick of det-inner
old_inner_close = "    </div>\n    </div>`;\n\n  document.getElementById('det-lvls')"
new_inner_close  = "    </div>\n    </div>\n    ${infoHtml}`;\n\n  document.getElementById('det-lvls')"
if old_inner_close in html:
    html = html.replace(old_inner_close, new_inner_close)
    print("  ✓ infoHtml appended to det-inner")
else:
    # Try alternate pattern
    old2 = "    </div>`;\n\n  document.getElementById('det-lvls')"
    new2 = "    </div>\n    ${infoHtml}`;\n\n  document.getElementById('det-lvls')"
    if old2 in html:
        html = html.replace(old2, new2, 1)
        print("  ✓ infoHtml appended (alt pattern)")
    else:
        print("  ✗ det-inner close not found")


# Restructure det-modal: add #det-info beside card column
html = html.replace(
    '<div class="ic" id="det-ic">\n      <div class="ic-inner" id="det-inner"></div>\n    </div>\n    <div class="ic-lvls" id="det-lvls"></div>',
    '<div class="ic-det-row">\n      <div id="det-ic-wrap">\n        <div class="ic" id="det-ic"><div class="ic-inner" id="det-inner"></div></div>\n        <div class="ic-lvls" id="det-lvls"></div>\n      </div>\n      <div id="det-info"></div>\n    </div>'
)

# CSS for new layout
det_layout_css = """
#det-modal{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;z-index:200}
#det-modal.h{display:none}
.ic-det-row{display:flex;gap:0;align-items:flex-start;position:relative;max-height:90vh}
#det-ic-wrap{flex-shrink:0}
#det-info{width:280px;max-height:90vh;overflow-y:auto;background:#060e18;
  border:1px solid #1a3040;border-left:none;border-radius:0 9px 9px 0;
  padding:10px 14px;display:flex;flex-direction:column;gap:0}
#det-close{position:absolute;top:-12px;right:-12px;width:26px;height:26px;z-index:10;
  border-radius:50%;background:#cc2222;border:2px solid #ff4444;
  color:#fff;font-size:14px;font-weight:900;cursor:pointer;
  display:flex;align-items:center;justify-content:center}
"""
# Replace existing det-modal CSS block
import re
html = re.sub(r'#det-modal\{[^}]+\}', '', html, count=1)
html = html.replace('.ic{width:auto;max-width:600px;display:flex;gap:0;flex-direction:row;position:relative}', det_layout_css + '.ic{width:245px;position:relative}', 1)
print("  ✓ det-modal restructured with side info panel")

# Update renderDet to set #det-info separately instead of appending infoHtml to det-inner
# Remove ${infoHtml} from inside det-inner template
html = html.replace("\n    ${infoHtml}`;\n\n  document.getElementById('det-lvls')",
                    "`;\n  document.getElementById('det-info').innerHTML=infoHtml;\n  document.getElementById('det-lvls')")
print("  ✓ infoHtml moved to #det-info element")


# Remove fusion recipe from card detail template
html = html.replace(
    '${fusHtml}\n    <div class="ic-bot">',
    '<div class="ic-bot">'
)
print("  ✓ Fusion recipe section removed from detail view")


# ID sort button in topbar
html = html.replace(
    '>Name    <span class="sort-arrow">↑</span></div>\n      <div class="sort-btn"',
    '>Name    <span class="sort-arrow">↑</span></div>\n      <div class="sort-btn"        data-sort="id"       onclick="setSort(\'id\')"      >ID      <span class="sort-arrow"></span></div>\n      <div class="sort-btn"'
)
print("  ✓ ID sort button added")


# -- Summon features --

# swapToCard function
html = html.replace('\nfunction load(){', '\nfunction swapToCard(cardId, level) {\n  const newCard = cards.find(r => String(r.id) === String(cardId));\n  if(!newCard) return;\n  selCard = newCard; selLvl = level || 0;\n  renderDet(newCard, selLvl);\n}\n' + '\nfunction load(){', 1)
print("  ✓ swapToCard function added")

# Load summonedBy
html = html.replace(
    "baseFusFrom=d.base_fusion_from||{}; baseFusTo=d.base_fusion_to||{};",
    "baseFusFrom=d.base_fusion_from||{}; baseFusTo=d.base_fusion_to||{}; summonedBy=d.summoned_by||{};"
)
html = html.replace(
    "let fusFrom={}, fusTo={}, idToName={}, baseFusFrom={}, baseFusTo={};",
    "let fusFrom={}, fusTo={}, idToName={}, baseFusFrom={}, baseFusTo={}, summonedBy={};"
)
print("  ✓ summonedBy loaded")

# Trigger prefix
html = html.replace(
    "      if(sk.trigger) lbl+=' ['+sk.trigger+']';",
    "      // trigger shown as prefix"
)
html = html.replace(
    "      let lbl=dispName;\n      if(sk.all==='1') lbl+=' All';",
    "      const trigPfx = sk.trigger==='death'?'On Death: ':sk.trigger==='play'?'On Play: ':'';\n"
    "      let lbl=dispName;\n      if(sk.all==='1') lbl+=' All';"
)
html = html.replace(
    '        <div class="ic-sk-txt" style="color:${col}">${lbl}</div>',
    '        <div class="ic-sk-txt" style="color:${col}">${trigPfx}${lbl}</div>'
)
print("  ✓ Trigger prefix")

# Summon panel JS
html = html.replace(
    "  document.getElementById('det-info').innerHTML=infoHtml;",
    """  document.getElementById('det-info').innerHTML=infoHtml;

  const _sumPanels = [];
  const _curSkills = d.skills||[];
  const _sumSkill  = _curSkills.find(sk=>sk.id==='summon'&&sk.card_id);
  if(_sumSkill) {
    const _sumCid   = String(_sumSkill.card_id);
    const _sumName  = idToName[_sumCid]||('ID:'+_sumCid);
    const _sumCard  = cards.find(r=>String(r.id)===_sumCid||r.upgrades?.some(u=>String(u.id)===_sumCid));
    const _sumLevel = _sumCard ? (_sumCard.upgrades?.findIndex(u=>String(u.id)===_sumCid)+2||1) : 1;
    const _sumSrc   = _sumCard ? imgSrc(lvlD(_sumCard,_sumLevel-1).picture) : '';
    _sumPanels.push({dir:'↓',label:'Summons',card:_sumCard,level:_sumLevel,src:_sumSrc,name:_sumName});
  }
  const _byIds = summonedBy[String(d.id||c.id)]||summonedBy[String(c.id)]||[];
  _byIds.forEach(byBaseId=>{
    const _byCard = cards.find(r=>String(r.id)===String(byBaseId));
    if(_byCard){
      const _bySrc = imgSrc(maxD(_byCard).picture);
      _sumPanels.push({dir:'↑',label:'Summoned by',card:_byCard,level:maxD(_byCard).upgrades?.length+1||1,src:_bySrc,name:_byCard.name});
    }
  });
  const _sumContainer = document.getElementById('det-summon');
  if(_sumContainer){
    if(_sumPanels.length){
      _sumContainer.style.display='flex';
      _sumContainer.innerHTML = _sumPanels.map(p=>{
        if(!p.card) return `<div class="det-sum-label">${p.dir} ${p.label}: ${p.name}</div>`;
        const sc=p.card, sl=p.level-1, sd=lvlD(sc,sl), sf=FAC[sc.type]||FAC['0'];
        const ssrc=imgSrc(sd.picture||'');
        const sdots=Math.min(Math.max(Math.ceil((parseInt(maxD(sc).health)||0)/5),1),8);
        const sskData=sd.skills&&sd.skills.length?sd.skills:sc.skills;
        let sskHtml='';
        sskData.forEach(sk=>{
          const col=SCOL[sk.id]||'#aabbcc', dispName=skNames[sk.id]||sk.id;
          const tp2=sk.trigger==='death'?'On Death: ':sk.trigger==='play'?'On Play: ':'';
          let l2=dispName;
          if(sk.all==='1') l2+=' All';
          if(sk.s) l2+=' '+(skNames[sk.s]||sk.s);
          if(sk.s2) l2+=' → '+(skNames[sk.s2]||sk.s2);
          if(sk.y&&sk.y!=='0') l2+=' '+(FAC_NAMES[sk.y]||sk.y);
          if(sk.x) l2+=' '+sk.x;
          if(sk.n&&sk.n!=='1') l2+=' ('+sk.n+' targets)';
          if(sk.c) l2+=' every '+sk.c;
          const su2=_renderSkillIcon(sk.id);
          const ii2=su2?`<img src="${su2}" style="width:13px;height:13px;image-rendering:pixelated">`:
            `<svg viewBox="0 0 32 32" style="fill:${col};color:${col}">${SPATH[sk.id]||''}</svg>`;
          sskHtml+=`<div class="ic-sk"><div class="ic-sk-ico" style="border:1px solid ${col}33;background:${col}12">${ii2}</div>
            <div class="ic-sk-txt" style="color:${col}">${tp2}${l2}</div></div>`;
        });
        return `<div class="det-sum-block">
          <div class="det-sum-label">${p.dir} <span>${p.label}</span></div>
          <div class="ic det-sum-ic" style="--fc:${sf.color}88;--cc:${sf.color}" onclick="swapToCard('${sc.id}',${sl})">
            <div class="ic-inner">
              <div class="ic-hdr" style="--hdr-top:${sf.hTop};--hdr-bot:${sf.hBot}">
                <div class="ic-type-wrap" style="border-color:${sf.color}55;background:${sf.color}15">${typeIcon(sc.type,sc.unit_type,sf.color)}</div>
                <div class="ic-cardname">${sc.name}</div>
                <div class="ic-costbadge">${sd.cost||0}</div>
              </div>
              <div class="ic-art">${ssrc?`<img src="${ssrc}" alt="" onerror="this.style.display='none'">`:
                `<div class="ic-art-noimg">No image</div>`}
                <div class="ic-fac-strip">
                  <div class="ic-fac-name" style="color:${sf.color}">${sf.name}</div>
                  <div class="ic-fac-set">${SETS[sc.set]||sc.set} · ${RAR[String(sc.rarity)]?.name||'?'} · ${sc.unit_type}</div>
                </div>
              </div>
              <div class="ic-skills">${sskHtml}</div>
              <div class="ic-bot">
                <div class="ic-atk-wrap"><svg class="ic-atk-ico" viewBox="0 0 32 32" style="fill:#ff8844;color:#ff8844">${SPATH.hunt||''}</svg>
                  <div class="ic-atk-val">${sd.attack||0}</div></div>
                <div class="ic-dots">${'<div class="hpdot"></div>'.repeat(sdots)}</div>
                <div class="ic-hp-right"><div class="ic-hp-val">${sd.health||0}</div></div>
              </div>
            </div>
          </div>
        </div>`;
      }).join('');
    } else {
      _sumContainer.style.display='none';
    }
  }"""
)
print("  ✓ Summon panel JS")

# det-summon div in modal
html = html.replace(
    '      <div id="det-info"></div>\n    </div>',
    '      <div id="det-info"></div>\n    </div>\n    <div id="det-summon" style="display:none;flex-direction:column;gap:8px;padding:10px 0 10px 10px;align-items:flex-start"></div>'
)
print("  ✓ det-summon div")

# Summon CSS
sum_css = """
#det-summon{min-width:100px}
.det-sum-row{display:flex;flex-direction:column;align-items:center;gap:4px}
.det-sum-arrow{font-size:11px;color:#3a6088;display:flex;align-items:center;gap:4px;white-space:nowrap}
.det-sum-arrow span{color:#5577aa;font-size:10px}
.det-sum-block{display:flex;flex-direction:column;gap:6px}
.det-sum-label{font-size:11px;color:#3a6088;display:flex;align-items:center;gap:5px}
.det-sum-label span{color:#5577aa}
.det-sum-ic{cursor:pointer;transition:filter .15s}
.det-sum-ic:hover{filter:brightness(1.15)}
.det-sum-chip{display:flex;align-items:center;gap:8px;padding:6px 10px;
  border-radius:5px;border:1px solid #1a3040;background:#080f18;cursor:pointer;transition:border-color .15s}
.det-sum-chip:hover{border-color:#3a6088}
.det-sum-compact .det-sum-label{margin-bottom:4px}
#det-summon{padding:8px 0 4px 0;display:flex;flex-direction:column;gap:12px}
"""
html = html.replace('#det-info{width:280px;', sum_css + '#det-info{width:280px;')
print("  ✓ Summon CSS")


# ic-hdr: remove position:absolute so header sits ABOVE artwork (not over it)
html = html.replace(
    '''.ic-hdr{height:46px;display:flex;align-items:center;padding:0 7px;gap:6px;
  position:absolute;top:0;left:0;right:0;z-index:2;
  background:linear-gradient(180deg,var(--hdr-top,#1a3448) 0%,var(--hdr-bot,#0e2030) 100%);
  border-bottom:1px solid rgba(0,0,0,.5)}''',
    '''.ic-hdr{height:46px;display:flex;align-items:center;padding:0 7px;gap:6px;
  background:linear-gradient(180deg,var(--hdr-top,#1a3448) 0%,var(--hdr-bot,#0e2030) 100%);
  border-bottom:1px solid rgba(0,0,0,.5)}'''
)
print("  ✓ ic-hdr: position:absolute removed, fully opaque")

# ATK_ICON / HP_ICON constants
atk_b64 = 'data:image/png;base64,' + base64.b64encode(open(os.path.join(ICONS_DIR,'Sprites','attack_icon32.png'),'rb').read()).decode()
hp_b64_icon  = 'data:image/png;base64,' + base64.b64encode(open(os.path.join(ICONS_DIR,'Sprites','health_icon32.png'),'rb').read()).decode()
html = html.replace(
    'const FACTION_ICONS = ',
    f'\nconst ATK_ICON = "{atk_b64}";\nconst HP_ICON  = "{hp_b64_icon}";\n' + 'const FACTION_ICONS = ',
    1
)
html = html.replace('<span class="ts ts-a">⚔${d.attack||0}</span>',
    '<span class="ts ts-a"><img src="${ATK_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle">${d.attack||0}</span>')
html = html.replace('<span class="ts ts-h">♥${d.health||0}</span>',
    '<span class="ts ts-h"><img src="${HP_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle">${d.health||0}</span>')
html = html.replace('<svg class="ic-atk-ico" viewBox="0 0 32 32" style="fill:#ff8844;color:#ff8844">${SPATH.hunt||\'\'}</svg>',
    '<img src="${ATK_ICON}" class="ic-atk-ico" style="image-rendering:pixelated">')
html = html.replace('<div class="ic-hp-val">${d.health||0}</div>',
    '<img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated;margin-right:3px"><div class="ic-hp-val">${d.health||0}</div>')
html = html.replace('<div class="ic-hp-val">${sd.health||0}</div>',
    '<img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated;margin-right:3px"><div class="ic-hp-val">${sd.health||0}</div>')
print("  ✓ ATK_ICON / HP_ICON injected")

# +20% font size for attack/health numbers
html = html.replace(
    ".ts{font-size:10px;font-weight:900;font-family:\'Impact\',sans-serif;\n  text-shadow:0 1px 3px #000,0 0 6px #000}",
    ".ts{font-size:12px;font-weight:900;font-family:\'Impact\',sans-serif;\n  text-shadow:0 1px 3px #000,0 0 6px #000}"
)
print("  ✓ Attack/Health font-size +20% tile only (10→12px)")

# Remove HP dots (ic-dots / hpdot)
import re as _re2
html = _re2.sub(r'\.ic-dots\{[^}]+\}\n\.hpdot\{[^}]+\}', '', html)
html = html.replace('\n  const dots=Math.min(Math.max(Math.ceil(hpMax/5),1),8);', '')
html = _re2.sub(r"\s*<div class=\"ic-dots\">\$\{.'<div class=\\"hpdot\\">'.*?repeat\((?:dots|sdots)\)\}</div>", '', html)
print("  ✓ HP dots removed")

# Tile: HP number left of icon, faction+level text color match card name
html = html.replace(
    '<span class="ts ts-h"><img src="${HP_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle">${d.health||0}</span>',
    '<span class="ts ts-h">${d.health||0}<img src="${HP_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle;margin-left:2px"></span>'
)
html = html.replace('.tile-sub{font-size:9px;color:#2a4055;margin-top:1px}',
                    '.tile-sub{font-size:9px;color:#bbc8d8;margin-top:1px}')
print("  ✓ Tile HP layout + tile-sub color")

# Detail: ic-fac-set (set/rarity/type below faction name in image) → #bbc8d8
html = html.replace(
    'ic-fac-set{font-size:9px;color:#3a5577;margin-top:1px;letter-spacing:.5px}',
    'ic-fac-set{font-size:9px;color:#bbc8d8;margin-top:1px;letter-spacing:.5px}'
)
print("  ✓ ic-fac-set color → #bbc8d8")

# Tile stats: proper flex layout for attack/health
html = html.replace(
    '.tile-stats{position:absolute;bottom:3px;left:0;right:0;\n  display:flex;justify-content:space-between;padding:0 4px;z-index:1}',
    '.tile-stats{position:absolute;bottom:3px;left:0;right:0;\n  display:flex;justify-content:space-between;align-items:center;padding:0 4px;z-index:1}\n.ts-a,.ts-h{display:flex;align-items:center;gap:2px}'
)
html = html.replace(
    '<span class="ts ts-a"><img src="${ATK_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle">${d.attack||0}</span>',
    '<div class="ts ts-a"><img src="${ATK_ICON}" style="width:12px;height:12px;image-rendering:pixelated"><span>${d.attack||0}</span></div>'
)
html = html.replace(
    '<span class="ts ts-h">${d.health||0}<img src="${HP_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle;margin-left:2px"></span>',
    '<div class="ts ts-h"><span>${d.health||0}</span><img src="${HP_ICON}" style="width:12px;height:12px;image-rendering:pixelated"></div>'
)
print("  ✓ Tile attack/health flex layout fixed")

# Fix .ts to have display:flex so icon and number sit side by side
html = html.replace(
    ".ts{font-size:12px;font-weight:900;font-family:\'Impact\',sans-serif;\n  text-shadow:0 1px 3px #000,0 0 6px #000}",
    ".ts{font-size:12px;font-weight:900;font-family:\'Impact\',sans-serif;\n  text-shadow:0 1px 3px #000,0 0 6px #000;display:flex;align-items:center;gap:2px}"
)
print("  ✓ .ts display:flex")

# Consolidate .ts CSS - remove duplicate rule, add line-height:1
html = html.replace(
    ".tile-stats{position:absolute;bottom:3px;left:0;right:0;\n  display:flex;justify-content:space-between;align-items:center;padding:0 4px;z-index:1}\n.ts-a,.ts-h{display:flex;align-items:center;gap:2px}\n.ts{font-size:12px;font-weight:900;font-family:\'Impact\',sans-serif;\n  text-shadow:0 1px 3px #000,0 0 6px #000;display:flex;align-items:center;gap:2px}\n.ts-a{color:#ff8844} .ts-h{color:#44dd55}",
    ".tile-stats{position:absolute;bottom:3px;left:0;right:0;\n  display:flex;justify-content:space-between;align-items:center;padding:0 4px;z-index:1}\n.ts{font-size:12px;font-weight:900;font-family:\'Impact\',sans-serif;line-height:1;\n  text-shadow:0 1px 3px #000,0 0 6px #000;display:flex;align-items:center;gap:3px}\n.ts-a{color:#ff8844} .ts-h{color:#44dd55}"
)
print("  ✓ .ts consolidated with line-height:1")

# Detail card: fix hp-right order - number then HP icon, remove ic-plus
html = html.replace(
    '<div class="ic-hp-right">\n        <img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated;margin-right:3px"><div class="ic-hp-val">${d.health||0}</div>\n        <div class="ic-plus">+</div>\n      </div>',
    '<div class="ic-hp-right">\n        <div class="ic-hp-val">${d.health||0}</div>\n        <img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated">\n      </div>'
)
print("  ✓ Detail hp-right: [number][HP icon], ic-plus removed")

# Remove circle border around faction icon in detail view
html = html.replace(
    'ic-type-wrap{width:32px;height:32px;flex-shrink:0;border-radius:50%;\n  border:2px solid rgba(255,255,255,.25);background:rgba(0,0,0,.4);\n  display:flex;align-items:center;justify-content:center;overflow:hidden}',
    'ic-type-wrap{width:32px;height:32px;flex-shrink:0;\n  display:flex;align-items:center;justify-content:center;overflow:hidden}'
)
print("  ✓ ic-type-wrap circle removed")

# Cost badge img: same size as faction icon (22px)
html = html.replace(
    '.ic-costbadge img{width:32px;height:32px;image-rendering:pixelated}',
    '.ic-costbadge img{width:22px;height:22px;image-rendering:pixelated}'
)
print("  ✓ Cost badge img 32→22px")

# Remove inline border/background from ic-type-wrap templates
html = html.replace(
    '"ic-type-wrap" style="border-color:${f.color}55;background:${f.color}15">',
    '"ic-type-wrap">'
)
html = html.replace(
    '"ic-type-wrap" style="border-color:${sf.color}55;background:${sf.color}15">',
    '"ic-type-wrap">'
)
print("  ✓ ic-type-wrap inline styles removed")

# Summon panel: fix hp-right order [number][HP icon]
html = html.replace(
    '<img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated;margin-right:3px"><div class="ic-hp-val">${sd.health||0}</div>',
    '<div class="ic-hp-val">${sd.health||0}</div><img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated">'
)
print("  ✓ Summon panel hp-right order fixed")

# Weaken icon: rotate 180° via CSS
html = html.replace(
    '.ic-sk-ico svg{width:13px;height:13px}',
    '''.ic-sk-ico svg{width:13px;height:13px}
.ic-sk-ico img[data-sk="weaken"]{transform:rotate(180deg)}
.fsb[data-sk="weaken"] img.sk-spr{transform:rotate(180deg)}'''
)
print("  ✓ Weaken icon 180° rotation CSS")

# Faction icon: use atlas image instead of SVG fallback in card header
html = html.replace(
    '${typeIcon(c.type,c.unit_type,f.color)}',
    '${FACTION_ICONS[c.type]?`<img src="${FACTION_ICONS[c.type]}" style="width:22px;height:22px;image-rendering:pixelated">`:typeIcon(c.type,c.unit_type,f.color)}'
)
html = html.replace(
    '${typeIcon(sc.type,sc.unit_type,sf.color)}',
    '${FACTION_ICONS[sc.type]?`<img src="${FACTION_ICONS[sc.type]}" style="width:22px;height:22px;image-rendering:pixelated">`:typeIcon(sc.type,sc.unit_type,sf.color)}'
)
print("  ✓ Faction icons: atlas image in card header")

# data-sk attribute on skill icon imgs (needed for weaken CSS rotation)
html = html.replace(
    '${_renderSkillIcon(sk.id)?`<img src="${_renderSkillIcon(sk.id)}" style="width:13px;height:13px;image-rendering:pixelated">`',
    '${_renderSkillIcon(sk.id)?`<img src="${_renderSkillIcon(sk.id)}" data-sk="${sk.id}" style="width:13px;height:13px;image-rendering:pixelated">`'
)
html = html.replace(
    'const ii2=su2?`<img src="${su2}" style="width:13px;height:13px;image-rendering:pixelated">`:',
    'const ii2=su2?`<img src="${su2}" data-sk="${sk.id}" style="width:13px;height:13px;image-rendering:pixelated">`:',
)
print("  ✓ data-sk attribute on skill icon imgs")

# Cost badge: replace metallic circle+number with atlas delay icon
# ic-costbadge CSS: remove radial-gradient background, make transparent container
html = html.replace(
    '''.ic-costbadge{position:absolute;top:-4px;right:-4px;width:28px;height:28px;
  background:radial-gradient(circle at 38% 32%,#e0e8f0,#96a8b8);
  border:2px solid #fff;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:900;color:#141c28;
  font-family:'Impact',sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.8);z-index:10}''',
    '''.ic-costbadge{position:absolute;top:-4px;right:-4px;width:32px;height:32px;
  display:flex;align-items:center;justify-content:center;z-index:10}
.ic-costbadge img{width:32px;height:32px;image-rendering:pixelated}
.ic-costbadge span{font-size:13px;font-weight:900;color:#fff;
  font-family:'Impact',sans-serif;background:#1a3448;border-radius:50%;
  width:28px;height:28px;display:flex;align-items:center;justify-content:center;
  border:2px solid #99aabc;box-shadow:0 2px 8px rgba(0,0,0,.8)}'''
)
print("  ✓ ic-costbadge CSS updated for atlas icon")

# Replace costbadge content in renderDet main card
html = html.replace(
    '<div class="ic-costbadge">${d.cost||0}</div>',
    '<div class="ic-costbadge">${DELAY_ICONS[String(d.cost||0)]?`<img src="${DELAY_ICONS[String(d.cost||0)]}" title="Cost ${d.cost||0}">`:'<span>'+( d.cost||0)+'</span>'}</div>'
)
# Summon panel cards use sd.cost
html = html.replace(
    '<div class="ic-costbadge">${sd.cost||0}</div>',
    '<div class="ic-costbadge">${DELAY_ICONS[String(sd.cost||0)]?`<img src="${DELAY_ICONS[String(sd.cost||0)]}" title="Cost ${sd.cost||0}">`:'<span>'+(sd.cost||0)+'</span>'}</div>'
)
print("  ✓ Cost badge uses atlas delay icon")

# tile-cost in grid view: same atlas delay icon
old_tile_css = '''.tile-cost{position:absolute;top:3px;right:3px;width:21px;height:21px;
  background:radial-gradient(circle at 38% 32%,#d8e0e8,#8898aa);
  border:2px solid #eee;border-radius:50%;z-index:2;
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:900;color:#141c28;font-family:\'Impact\',sans-serif;
  box-shadow:0 2px 6px rgba(0,0,0,.7)}'''
new_tile_css = '''.tile-cost{position:absolute;top:2px;right:2px;width:28px;height:28px;
  z-index:2;display:flex;align-items:center;justify-content:center}
.tile-cost img{width:20px;height:20px;image-rendering:pixelated}
.tile-cost span{font-size:9px;font-weight:900;color:#fff;font-family:\'Impact\',sans-serif;
  background:#1a3448;border-radius:50%;width:16px;height:16px;
  display:flex;align-items:center;justify-content:center;
  border:2px solid #99aabc;box-shadow:0 2px 6px rgba(0,0,0,.7)}'''
html = html.replace(old_tile_css, new_tile_css)
html = html.replace(
    '${d.cost?`<div class="tile-cost">${d.cost}</div>`:'\'\'}'  ,
    '${d.cost!==undefined?`<div class="tile-cost">${DELAY_ICONS[String(d.cost)]?\'<img src="\'+DELAY_ICONS[String(d.cost)]+\'">\':'<span>\'+d.cost+\'</span>\'}</div>`:'\'\'}'
)
print("  ✓ Tile cost icon uses atlas delay icon")

# ic-costbadge: no longer absolute, sits as flex item in header row
html = html.replace(
    '''.ic-costbadge{position:absolute;top:-4px;right:-4px;width:28px;height:28px;
  background:radial-gradient(circle at 38% 32%,#e0e8f0,#96a8b8);
  border:2px solid #fff;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:900;color:#141c28;
  font-family:\'Impact\',sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.8);z-index:10}''',
    '''.ic-costbadge{width:32px;height:32px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center}
.ic-costbadge img{width:32px;height:32px;image-rendering:pixelated}
.ic-costbadge span{font-size:13px;font-weight:900;color:#fff;
  font-family:\'Impact\',sans-serif;background:#1a3448;border-radius:50%;
  width:28px;height:28px;display:flex;align-items:center;justify-content:center;
  border:2px solid #99aabc;box-shadow:0 2px 8px rgba(0,0,0,.8)}'''
)
print("  ✓ ic-costbadge repositioned as flex item in header")

# tile-fdot: replace colored dot with atlas faction icon
html = html.replace(
    '''.tile-fdot{position:absolute;top:3px;left:3px;width:8px;height:8px;
  border-radius:50%;border:1px solid rgba(255,255,255,.25);z-index:2}
[data-t="1"] .tile-fdot{background:var(--f1)} [data-t="2"] .tile-fdot{background:var(--f2)}
[data-t="3"] .tile-fdot{background:var(--f3)} [data-t="4"] .tile-fdot{background:var(--f4)}
[data-t="5"] .tile-fdot{background:var(--f5)} [data-t="6"] .tile-fdot{background:var(--f6)}''',
    '''.tile-fdot{position:absolute;top:2px;left:2px;width:15px;height:15px;z-index:2;
  display:flex;align-items:center;justify-content:center}
.tile-fdot img{width:15px;height:15px;image-rendering:pixelated;
  filter:drop-shadow(0 1px 2px rgba(0,0,0,.8))}'''
)
html = html.replace(
    '<div class="tile-fdot"></div>',
    '<div class="tile-fdot">${FACTION_ICONS[c.type]?`<img src="${FACTION_ICONS[c.type]}" alt="">`:'\'\'}</div>'
)
print("  ✓ Tile faction icon: atlas image replaces colored dot")

# Fusion icon in tile footer (name bar), HP stays in image
html = html.replace(
    '''.tile-name{padding:3px 5px 4px;background:#080f1c;font-size:11px;font-weight:700;
  color:#bbc8d8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.2}
.tile-sub{font-size:9px;color:#2a4055;margin-top:1px}''',
    '''.tile-name{padding:3px 5px 4px;background:#080f1c;font-size:11px;font-weight:700;
  color:#bbc8d8;line-height:1.2;display:flex;align-items:center;justify-content:space-between;gap:4px}
.tile-name-text{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.tile-sub{font-size:9px;color:#2a4055;margin-top:1px}
.tile-fus{width:15px;height:15px;flex-shrink:0;display:flex;align-items:center;justify-content:center}
.tile-fus img{width:15px;height:15px;image-rendering:pixelated;
  filter:drop-shadow(0 1px 2px rgba(0,0,0,.9))}'''
)
html = html.replace(
    '''      <div class="tile-name">${c.name||('(ID:'+c.id+')')}
        <div class="tile-sub">${f.name} · Lv.${maxL}${c.unit_type!=='assault'?' · '+c.unit_type:''}</div>
      </div>''',
    '''      <div class="tile-name"><div class="tile-name-text">${c.name||('(ID:'+c.id+')')}
        <div class="tile-sub">${f.name} · Lv.${maxL}${c.unit_type!=='assault'?' · '+c.unit_type:''}</div>
      </div>${FUSION_ICONS[String(c.fusion_level||0)]?`<div class="tile-fus"><img src="${FUSION_ICONS[String(c.fusion_level||0)]}"></div>`:''}</div>'''
)
print("  ✓ Fusion icon in tile footer, HP stays in image")

# Remove HP dots (ic-dots / hpdot) - not useful
import re as _re
html = _re.sub(r'\.ic-dots\{[^}]+\}
\.hpdot\{[^}]+\}', '', html)
html = html.replace('\n  const dots=Math.min(Math.max(Math.ceil(hpMax/5),1),8);', '')
html = html.replace('<div class="ic-dots">${\'<div class="hpdot"></div>\'.repeat(dots)}</div>\n      <div class="ic-hp-right">', '<div class="ic-hp-right">')
html = _re.sub(r'\s*const sdots=Math\.min[^\n]+', '', html)
html = _re.sub(r'\s*<div class="ic-dots">\$\{[\'"]<div class=\\\"hpdot\\\"></div>[\'"]\.[^}]+\}</div>', '', html)
print("  ✓ HP dots removed")

# Tile: HP number left of icon, faction+level text color match card name
html = html.replace(
    '<span class="ts ts-h"><img src="${HP_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle">${d.health||0}</span>',
    '<span class="ts ts-h">${d.health||0}<img src="${HP_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle;margin-left:2px"></span>'
)
html = html.replace('.tile-sub{font-size:9px;color:#2a4055;margin-top:1px}',
                    '.tile-sub{font-size:9px;color:#bbc8d8;margin-top:1px}')
print("  ✓ Tile HP layout + tile-sub color")

# Detail: ic-fac-set (set/rarity/type below faction name in image) → #bbc8d8
html = html.replace(
    'ic-fac-set{font-size:9px;color:#3a5577;margin-top:1px;letter-spacing:.5px}',
    'ic-fac-set{font-size:9px;color:#bbc8d8;margin-top:1px;letter-spacing:.5px}'
)
print("  ✓ ic-fac-set color → #bbc8d8")

# Tile stats: proper flex layout for attack/health
html = html.replace(
    '.tile-stats{position:absolute;bottom:3px;left:0;right:0;\n  display:flex;justify-content:space-between;padding:0 4px;z-index:1}',
    '.tile-stats{position:absolute;bottom:3px;left:0;right:0;\n  display:flex;justify-content:space-between;align-items:center;padding:0 4px;z-index:1}\n.ts-a,.ts-h{display:flex;align-items:center;gap:2px}'
)
html = html.replace(
    '<span class="ts ts-a"><img src="${ATK_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle">${d.attack||0}</span>',
    '<div class="ts ts-a"><img src="${ATK_ICON}" style="width:12px;height:12px;image-rendering:pixelated"><span>${d.attack||0}</span></div>'
)
html = html.replace(
    '<span class="ts ts-h">${d.health||0}<img src="${HP_ICON}" style="width:12px;height:12px;image-rendering:pixelated;vertical-align:middle;margin-left:2px"></span>',
    '<div class="ts ts-h"><span>${d.health||0}</span><img src="${HP_ICON}" style="width:12px;height:12px;image-rendering:pixelated"></div>'
)
print("  ✓ Tile attack/health flex layout fixed")

# Fix .ts to have display:flex so icon and number sit side by side
html = html.replace(
    ".ts{font-size:12px;font-weight:900;font-family:\'Impact\',sans-serif;\n  text-shadow:0 1px 3px #000,0 0 6px #000}",
    ".ts{font-size:12px;font-weight:900;font-family:\'Impact\',sans-serif;\n  text-shadow:0 1px 3px #000,0 0 6px #000;display:flex;align-items:center;gap:2px}"
)
print("  ✓ .ts display:flex")

# Consolidate .ts CSS - remove duplicate rule, add line-height:1
html = html.replace(
    ".tile-stats{position:absolute;bottom:3px;left:0;right:0;\n  display:flex;justify-content:space-between;align-items:center;padding:0 4px;z-index:1}\n.ts-a,.ts-h{display:flex;align-items:center;gap:2px}\n.ts{font-size:12px;font-weight:900;font-family:\'Impact\',sans-serif;\n  text-shadow:0 1px 3px #000,0 0 6px #000;display:flex;align-items:center;gap:2px}\n.ts-a{color:#ff8844} .ts-h{color:#44dd55}",
    ".tile-stats{position:absolute;bottom:3px;left:0;right:0;\n  display:flex;justify-content:space-between;align-items:center;padding:0 4px;z-index:1}\n.ts{font-size:12px;font-weight:900;font-family:\'Impact\',sans-serif;line-height:1;\n  text-shadow:0 1px 3px #000,0 0 6px #000;display:flex;align-items:center;gap:3px}\n.ts-a{color:#ff8844} .ts-h{color:#44dd55}"
)
print("  ✓ .ts consolidated with line-height:1")

# Detail card: fix hp-right order - number then HP icon, remove ic-plus
html = html.replace(
    '<div class="ic-hp-right">\n        <img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated;margin-right:3px"><div class="ic-hp-val">${d.health||0}</div>\n        <div class="ic-plus">+</div>\n      </div>',
    '<div class="ic-hp-right">\n        <div class="ic-hp-val">${d.health||0}</div>\n        <img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated">\n      </div>'
)
print("  ✓ Detail hp-right: [number][HP icon], ic-plus removed")

# Remove circle border around faction icon in detail view
html = html.replace(
    'ic-type-wrap{width:32px;height:32px;flex-shrink:0;border-radius:50%;\n  border:2px solid rgba(255,255,255,.25);background:rgba(0,0,0,.4);\n  display:flex;align-items:center;justify-content:center;overflow:hidden}',
    'ic-type-wrap{width:32px;height:32px;flex-shrink:0;\n  display:flex;align-items:center;justify-content:center;overflow:hidden}'
)
print("  ✓ ic-type-wrap circle removed")

# Cost badge img: same size as faction icon (22px)
html = html.replace(
    '.ic-costbadge img{width:32px;height:32px;image-rendering:pixelated}',
    '.ic-costbadge img{width:22px;height:22px;image-rendering:pixelated}'
)
print("  ✓ Cost badge img 32→22px")

# Remove inline border/background from ic-type-wrap templates
html = html.replace(
    '"ic-type-wrap" style="border-color:${f.color}55;background:${f.color}15">',
    '"ic-type-wrap">'
)
html = html.replace(
    '"ic-type-wrap" style="border-color:${sf.color}55;background:${sf.color}15">',
    '"ic-type-wrap">'
)
print("  ✓ ic-type-wrap inline styles removed")

# Summon panel: fix hp-right order [number][HP icon]
html = html.replace(
    '<img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated;margin-right:3px"><div class="ic-hp-val">${sd.health||0}</div>',
    '<div class="ic-hp-val">${sd.health||0}</div><img src="${HP_ICON}" style="width:20px;height:20px;image-rendering:pixelated">'
)
print("  ✓ Summon panel hp-right order fixed")

# Final: write output
print("\nWriting output...")
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

size = os.path.getsize(OUT_FILE)//1024
print(f"Output: {OUT_FILE} ({size} KB)")

# Syntax check
script_start = html.rfind('<script>') + len('<script>')
script_end   = html.rfind('</script>')
with open('/tmp/check.js','w') as f:
    f.write(html[script_start:script_end])

result = subprocess.run(['node','--check','/tmp/check.js'], capture_output=True, text=True)
if result.returncode == 0:
    print("✓ SYNTAX OK")
else:
    print("✗ SYNTAX ERROR:")
    print(result.stderr[:300])

