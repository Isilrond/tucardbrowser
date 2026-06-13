const { app, BrowserWindow, protocol, net, ipcMain } = require('electron')
const path = require('path')
const fs   = require('fs')
const http = require('http')

protocol.registerSchemesAsPrivileged([
  { scheme: 'tu-img', privileges: { secure: true, standard: true, stream: true } }
])

// ── Game server XML URLs ──────────────────────────────────────────────────────
const BASE_URL   = 'http://mobile.tyrantonline.com/assets'
const XML_SECTIONS = Array.from({length: 21}, (_, i) => `cards_section_${i+1}.xml`)
const XML_EXTRA    = ['skills_set.xml', 'fusion_recipes_cj2.xml']
const ALL_XMLS     = [...XML_SECTIONS, ...XML_EXTRA]
// ─────────────────────────────────────────────────────────────────────────────

const USER_DATA_DIR  = app.getPath('userData')
const CACHED_JSON    = path.join(USER_DATA_DIR, 'tu_data.json')
const CACHED_ETAGS   = path.join(USER_DATA_DIR, 'tu_etags.json')
const CACHED_XML_DIR = path.join(USER_DATA_DIR, 'xml_cache')

const BUNDLED_JSON = app.isPackaged
  ? path.join(process.resourcesPath, 'tu_data.json')
  : path.join(__dirname, 'tu_data.json')

// ── Simple XML text → object parser ──────────────────────────────────────────
function parseXML(xmlText) {
  // Returns { tag, attrs, children, text }
  const stack = []
  let root = null
  let pos = 0
  const len = xmlText.length

  const skipWhitespace = () => { while (pos < len && xmlText[pos] <= ' ') pos++ }
  const readUntil = (ch) => {
    const start = pos
    while (pos < len && xmlText[pos] !== ch) pos++
    return xmlText.slice(start, pos)
  }

  const parseAttrs = (raw) => {
    const attrs = {}
    const re = /(\w+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g
    let m
    while ((m = re.exec(raw)) !== null) attrs[m[1]] = m[2] !== undefined ? m[2] : m[3]
    return attrs
  }

  const decodeEntities = (s) => s
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&apos;/g, "'")

  while (pos < len) {
    skipWhitespace()
    if (pos >= len) break

    if (xmlText[pos] === '<') {
      pos++
      if (xmlText[pos] === '?') { // PI
        while (pos < len && !(xmlText[pos-1] === '?' && xmlText[pos] === '>')) pos++
        pos++; continue
      }
      if (xmlText[pos] === '!') { // comment or CDATA
        if (xmlText.slice(pos, pos+3) === '!--') {
          pos += 3
          while (pos < len && xmlText.slice(pos, pos+3) !== '-->') pos++
          pos += 3
        } else {
          while (pos < len && xmlText[pos] !== '>') pos++
          pos++
        }
        continue
      }
      if (xmlText[pos] === '/') { // closing tag
        pos++
        const tag = readUntil('>').trim()
        pos++
        if (stack.length > 0) {
          const node = stack.pop()
          if (stack.length > 0) stack[stack.length-1].children.push(node)
          else root = node
        }
        continue
      }
      // opening tag
      let tagContent = ''
      let selfClose = false
      while (pos < len) {
        const c = xmlText[pos++]
        if (c === '>') break
        if (c === '/' && xmlText[pos] === '>') { selfClose = true; pos++; break }
        tagContent += c
      }
      const spIdx = tagContent.search(/\s/)
      const tag   = spIdx === -1 ? tagContent : tagContent.slice(0, spIdx)
      const attrs = spIdx === -1 ? {} : parseAttrs(tagContent.slice(spIdx))
      const node  = { tag, attrs, children: [], text: '' }
      if (selfClose) {
        if (stack.length > 0) stack[stack.length-1].children.push(node)
        else root = node
      } else {
        stack.push(node)
      }
    } else {
      // text content
      const text = readUntil('<').trim()
      if (text && stack.length > 0) stack[stack.length-1].text = decodeEntities(text)
    }
  }
  return root || { tag: 'root', attrs: {}, children: [], text: '' }
}

function findChildren(node, tag) {
  if (!node || !node.children) return []
  return node.children.filter(c => c.tag === tag)
}
function findChild(node, tag) { return findChildren(node, tag)[0] || null }
function childText(node, tag) { const c = findChild(node, tag); return c ? c.text : null }

// ── Parse skills_set.xml ──────────────────────────────────────────────────────
function parseSkills(xml) {
  const root = parseXML(xml)
  const names = {}, descs = {}, descs_all = {}, descs_fac = {}, descs_all_fac = {}
  for (const node of findChildren(root, 'skillType')) {
    const id   = childText(node, 'id')   || node.attrs.id
    const name = childText(node, 'name') || node.attrs.name
    const desc         = childText(node, 'desc')             || node.attrs.desc     || ''
    const desc_all     = childText(node, 'desc_all')         || ''
    const desc_fac     = childText(node, 'desc_faction')     || ''
    const desc_all_fac = childText(node, 'desc_all_faction') || ''
    if (id && name) {
      names[id] = name
      descs[id] = desc
      if (desc_all)     descs_all[id]     = desc_all
      if (desc_fac)     descs_fac[id]     = desc_fac
      if (desc_all_fac) descs_all_fac[id] = desc_all_fac
    }
  }
  return { names, descs, descs_all, descs_fac, descs_all_fac }
}

// ── Parse fusion_recipes_cj2.xml ─────────────────────────────────────────────
function parseFusions(xml) {
  const root = parseXML(xml)
  const map = {}
  for (const fr of findChildren(root, 'fusion_recipe')) {
    const cardId   = childText(fr, 'card_id')
    const resources = findChildren(fr, 'resource').map(r => ({
      card_id: r.attrs.card_id,
      number:  r.attrs.number
    }))
    if (cardId) map[cardId] = resources
  }
  return map
}

// ── Parse cards_section_*.xml ─────────────────────────────────────────────────
function parseCards(xmlList) {
  const FACTION_MAP = {'1':'Imperial','2':'Raider','3':'Bloodthirsty','4':'Xeno','5':'Righteous','6':'Progenitor'}
  const cards = []

  for (const xml of xmlList) {
    const root = parseXML(xml)
    const units = root.tag === 'root'
      ? root.children.filter(c => c.tag === 'unit')
      : findChildren(root, 'unit')

    for (const unit of units) {
      const get = (tag) => childText(unit, tag)
      const id       = get('id')
      const name     = get('n')
      if (!id || !name) continue

      const picture   = get('picture') || ''
      const attack    = get('attack')  || '0'
      const health    = get('health')  || '0'
      const cost      = get('cost')    || '0'
      const rarity    = get('rarity')  || '1'
      const typeId    = get('type')    || '1'
      const setId     = get('set')     || '1000'
      const delay     = get('delay')   || '0'
      const fusionLvl    = get('fusion_level')   || '0'
      const assetBundle  = get('asset_bundle')   || ''

      const setNum = parseInt(setId)
      const unitType = setNum === 7000 ? 'commander'
                     : (setNum === 8000 || setNum === 8500) ? 'structure'
                     : 'assault'

      const skills = findChildren(unit, 'skill').map(s => ({
        id: s.attrs.id || s.text || '',
        x: s.attrs.x, y: s.attrs.y, s: s.attrs.s,
        all: s.attrs.all, trigger: s.attrs.trigger
      })).filter(s => s.id)

      // Upgrades
      const upgrades = []
      for (const upg of findChildren(unit, 'upgrade')) {
        const ul = {
          level:   childText(upg, 'level'),
          id:       childText(upg, 'card_id'),
          card_id: childText(upg, 'card_id'),
          attack:  childText(upg, 'attack'),
          health:  childText(upg, 'health'),
          picture: childText(upg, 'picture'),
          skills:  findChildren(upg, 'skill').map(s => ({
            id: s.attrs.id || s.text || '',
            x: s.attrs.x, y: s.attrs.y, s: s.attrs.s, s2: s.attrs.s2,
            n: s.attrs.n, c: s.attrs.c,
            all: s.attrs.all, trigger: s.attrs.trigger, card_id: s.attrs.card_id
          })).filter(s => s.id)
        }
        upgrades.push(ul)
      }

      const maxLevel = upgrades.length > 0
        ? parseInt(upgrades[upgrades.length-1].level || '1')
        : 1

      cards.push({
        id, name, picture, attack: parseInt(attack), health: parseInt(health),
        cost: parseInt(cost), rarity: parseInt(rarity),
        type: unitType, faction: FACTION_MAP[typeId] || 'Unknown',
        faction_id: typeId, set: setId, delay: parseInt(delay),
        fusion_level: parseInt(fusionLvl), max_level: maxLevel,
        asset_bundle: assetBundle,
        skills, upgrades
      })
    }
  }
  return cards
}

// ── HTTP GET → Promise<string> ────────────────────────────────────────────────
function httpGet(url, headersOnly = false) {
  return new Promise((resolve, reject) => {
    const req = http.request(url, { method: headersOnly ? 'HEAD' : 'GET', timeout: 15000 }, (res) => {
      if (headersOnly) { res.resume(); return resolve(res.headers) }
      if (res.statusCode === 301 || res.statusCode === 302) {
        return httpGet(res.headers.location, headersOnly).then(resolve).catch(reject)
      }
      if (res.statusCode !== 200) { res.resume(); return reject(new Error(`HTTP ${res.statusCode} for ${url}`)) }
      const chunks = []
      res.on('data', c => chunks.push(c))
      res.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')))
      res.on('error', reject)
    })
    req.on('error', reject)
    req.on('timeout', () => { req.destroy(); reject(new Error(`Timeout: ${url}`)) })
    req.end()
  })
}

// ── Check & update XMLs ───────────────────────────────────────────────────────
async function checkAndUpdate(win) {
  try {
    fs.mkdirSync(CACHED_XML_DIR, { recursive: true })

    // Load cached ETags
    let etags = {}
    try { etags = JSON.parse(fs.readFileSync(CACHED_ETAGS, 'utf-8')) } catch {}

    win.webContents.send('update-status', { state: 'checking' })

    // Check each XML for changes via HEAD request
    const toDownload = []
    for (const file of ALL_XMLS) {
      const url = `${BASE_URL}/${file}`
      try {
        const headers = await httpGet(url, true)
        const etag    = headers.etag || headers['last-modified'] || ''
        const cached  = path.join(CACHED_XML_DIR, file)
        if (!fs.existsSync(cached) || etags[file] !== etag) {
          toDownload.push({ file, url, etag })
        }
      } catch (e) {
        console.log(`HEAD failed for ${file}:`, e.message)
        // If we have no cache, must download; otherwise skip
        if (!fs.existsSync(path.join(CACHED_XML_DIR, file))) {
          toDownload.push({ file, url, etag: '' })
        }
      }
    }

    if (toDownload.length === 0) {
      win.webContents.send('update-status', { state: 'up-to-date' })
      return
    }

    win.webContents.send('update-status', { state: 'downloading', count: toDownload.length })

    // Download changed XMLs
    for (let i = 0; i < toDownload.length; i++) {
      const { file, url, etag } = toDownload[i]
      win.webContents.send('update-status', {
        state: 'progress',
        pct: Math.round(i / toDownload.length * 80),
        file
      })
      const xml = await httpGet(url)
      fs.writeFileSync(path.join(CACHED_XML_DIR, file), xml, 'utf-8')
      etags[file] = etag
    }

    win.webContents.send('update-status', { state: 'progress', pct: 85, file: 'Parsing...' })

    // Re-parse all XMLs
    const cardXmls = XML_SECTIONS.map(f => {
      const p = path.join(CACHED_XML_DIR, f)
      return fs.existsSync(p) ? fs.readFileSync(p, 'utf-8') : ''
    }).filter(Boolean)

    const skillsPath  = path.join(CACHED_XML_DIR, 'skills_set.xml')
    const fusionPath  = path.join(CACHED_XML_DIR, 'fusion_recipes_cj2.xml')

    // Fallback to bundled JSON for skills/fusion if not downloaded yet
    let skillData = { names: {}, descs: {} }
    let fusionMap = {}
    if (fs.existsSync(skillsPath))  skillData = parseSkills(fs.readFileSync(skillsPath, 'utf-8'))
    if (fs.existsSync(fusionPath))  fusionMap = parseFusions(fs.readFileSync(fusionPath, 'utf-8'))

    win.webContents.send('update-status', { state: 'progress', pct: 92, file: 'Building...' })

    const cards = parseCards(cardXmls)
    const newData = {
      cards,
      skill_names:         skillData.names,
      skill_descs:         skillData.descs,
      skill_descs_all:     skillData.descs_all,
      skill_descs_fac:     skillData.descs_fac,
      skill_descs_all_fac: skillData.descs_all_fac,
      fusion_map:      fusionMap
    }

    fs.writeFileSync(CACHED_JSON,  JSON.stringify(newData))
    fs.writeFileSync(CACHED_ETAGS, JSON.stringify(etags))

    win.webContents.send('update-status', {
      state:   'done',
      version: new Date().toLocaleDateString('de-DE'),
      cards:   cards.length
    })

  } catch (err) {
    console.log('Update failed:', err.message)
    win.webContents.send('update-status', { state: 'offline', error: err.message })
  }
}

// ── Window ────────────────────────────────────────────────────────────────────
function createWindow () {
  const win = new BrowserWindow({
    width: 1400, height: 900, minWidth: 900, minHeight: 600,
    title: 'Tyrant Unleashed \u2013 Card Browser',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false,
    },
    backgroundColor: '#161c24', show: false,
  })
  win.setMenuBarVisibility(false)
  win.once('ready-to-show', () => { win.maximize(); win.show(); })
  win.loadFile(path.join(__dirname, 'src', 'index.html'))
  // Uncomment to debug: win.webContents.openDevTools()
  return win
}

// ── IPC: load data ────────────────────────────────────────────────────────────
ipcMain.handle('load-data', async (event) => {
  event.sender.send('load-progress', 30)
  const dataFile = fs.existsSync(CACHED_JSON) ? CACHED_JSON : BUNDLED_JSON
  console.log('Loading from:', dataFile)
  try {
    const raw = fs.readFileSync(dataFile, 'utf-8')
    event.sender.send('load-progress', 80)
    return raw
  } catch (err) {
    console.error('Failed to load data:', err)
    return null
  }
})

// ── App ───────────────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  const imagesDir = app.isPackaged
    ? path.join(process.resourcesPath, 'images')
    : path.join(__dirname, 'images')

  protocol.handle('tu-img', (request) => {
    try {
      const url  = new URL(request.url)
      let filename = url.hostname
      const extra  = url.pathname.replace(/^\/|\/$/g, '')
      if (extra) filename += '/' + extra
      const base = filename.replace(/\.(jpg|jpeg|png)$/i, '')
      for (const ext of ['.jpg', '.png', '.jpeg']) {
        const fp = path.join(imagesDir, base + ext)
        if (fs.existsSync(fp)) return net.fetch('file:///' + fp.replace(/\\/g, '/'))
      }
      return new Response('', { status: 404 })
    } catch { return new Response('', { status: 500 }) }
  })

  const win = createWindow()
  win.webContents.once('did-finish-load', () => checkAndUpdate(win))

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
