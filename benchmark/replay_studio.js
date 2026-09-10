/* Replay Studio v2 — board with card art + interactive decision graph.
 * Inlined into replay_studio_template.html by replay_studio.py. Expects the
 * JSON payload blocks #meta, #frames, #cards (see replay_studio.py for the
 * frame schema). Exposes window.__replay for replay_video.js. */
(function () {
'use strict';
const META = JSON.parse(document.getElementById('meta').textContent);
const FRAMES = JSON.parse(document.getElementById('frames').textContent);
const CARDS = JSON.parse(document.getElementById('cards').textContent);
const N = FRAMES.length;
const PRESENT = new URLSearchParams(location.search).get('present') === '1';
if (PRESENT) document.body.classList.add('present');

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const STEPS = ['UN', 'UP', 'DR', 'M1', 'BC', 'DA', 'DB', 'FCD', 'CD', 'EC', 'M2', 'ET', 'CL'];
const KINDLBL = {priority: 'priority window', target: 'choose target', choose: 'choice', blockers: 'declare blockers',
  attackers: 'declare attackers', mulligan: 'mulligan', leaf_eval: 'search', turn_plan: 'turn plan', mode: 'choose mode',
  use: 'yes / no', announce_x: 'choose X'};
const CHIPLBL = {pilot: 'Pilot', auto: 'Auto', fallback: 'Fallback', search: 'Search', planning: 'Plan', plan: 'Plan-executed', event: 'Game'};

$('title').textContent = META.title || 'Replay';
$('subtitle').textContent = META.subtitle || '';
$('nameA').textContent = META.playerA || 'A';
$('nameB').textContent = META.playerB || 'B';
$('footer').textContent = `${N} frames · ` + Object.entries(META.counts || {}).map(([k, v]) => `${v} ${k}`).join(' · ')
  + (META.result ? ` · result: ${JSON.stringify(META.result)}` : '');

// ---------- card images ----------
function stubSvg(card, name) {
  const c = card || {};
  const nm = esc(name || c.name || '?');
  const tl = esc(c.type_line || '');
  const pt = c.power != null ? `${c.power}/${c.toughness}` : (c.loyalty != null ? `L${c.loyalty}` : '');
  const col = {W: '#e8e2c8', U: '#7fb3e0', B: '#6b6470', R: '#e08a6a', G: '#7fbb8a'}[(c.color || '')[0]] || '#b8ad98';
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='146' height='204' viewBox='0 0 146 204'>
<rect x='2' y='2' width='142' height='200' rx='10' fill='#1d1d1d' stroke='${col}' stroke-width='4'/>
<rect x='12' y='30' width='122' height='90' rx='4' fill='${col}' opacity='.35'/>
<text x='73' y='22' font-family='sans-serif' font-size='11' font-weight='700' fill='#eee' text-anchor='middle'>${nm.length > 22 ? nm.slice(0, 21) + '…' : nm}</text>
<text x='73' y='138' font-family='sans-serif' font-size='9' fill='#ccc' text-anchor='middle'>${tl.length > 26 ? tl.slice(0, 25) + '…' : tl}</text>
<text x='128' y='194' font-family='monospace' font-size='13' font-weight='700' fill='#eee' text-anchor='end'>${pt}</text></svg>`;
  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
}
const BACK = 'data:image/svg+xml;utf8,' + encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='146' height='204'><rect x='2' y='2' width='142' height='200' rx='10' fill='#3b2a5a' stroke='#8a6dbf' stroke-width='4'/><circle cx='73' cy='102' r='34' fill='none' stroke='#8a6dbf' stroke-width='5'/></svg>`);

function imgSources(key, size, name) {
  const c = CARDS[key] || {};
  const list = (size === 'normal' ? c.img_normal : c.img_small) || c.img_small || [];
  return list.length ? list.slice() : [];
}
function setImg(img, key, size, name) {
  const srcs = imgSources(key, size, name);
  const card = CARDS[key];
  img.alt = name || (card && card.name) || '';
  img.draggable = false;
  const stub = stubSvg(card, name);
  let i = 0;
  const next = () => { if (i < srcs.length) img.src = srcs[i++]; else img.src = stub; };
  img.onerror = () => { if (img.src !== stub) next(); };
  next();
}

// ---------- board ----------
let prevIds = new Set(), prevLife = {A: null, B: null};
const HANDHIDE = {B: false};

function cardEl(ref, opts) {
  opts = opts || {};
  const card = CARDS[ref.key] || {};
  const d = document.createElement('div');
  d.className = 'c' + (ref.tapped ? ' tapped' : '') + (ref.sick ? ' sick' : '') + (ref.attacking ? ' attacking' : '')
    + (ref.blocking ? ' blocking' : '') + (opts.enter ? ' enter' : '') + (ref.face_down ? ' fd' : '') + (ref.token ? ' token' : '');
  d.dataset.id = ref.id; d.dataset.key = ref.key || '';
  const img = document.createElement('img');
  if (ref.face_down || opts.hidden) img.src = BACK; else setImg(img, ref.transformed && card.back ? backKey(ref.key) : ref.key, 'small', ref.name);
  d.appendChild(img);
  if (ref.power != null) {
    const pt = document.createElement('div');
    pt.className = 'pt' + (ref.damage ? ' hurt' : '');
    pt.textContent = `${ref.power}/${ref.toughness}` + (ref.damage ? ` −${ref.damage}` : '');
    d.appendChild(pt);
  }
  if (ref.loyalty != null) { const l = document.createElement('div'); l.className = 'loy'; l.textContent = ref.loyalty; d.appendChild(l); }
  const ctr = Object.entries(ref.counters || {}).filter(([k]) => k !== 'loyalty');
  if (ctr.length) {
    const b = document.createElement('div'); b.className = 'ctr';
    b.textContent = ctr.map(([k, v]) => `${k} ×${v}`).join(' ');
    d.appendChild(b);
  }
  if (ref.sick && ref.power != null) { const s = document.createElement('div'); s.className = 'badge sickb'; s.textContent = 'zz'; s.title = 'summoning sick'; d.appendChild(s); }
  if (opts.attachments && opts.attachments.length) {
    opts.attachments.forEach((a, i) => {
      const ae = document.createElement('div'); ae.className = 'att'; ae.style.setProperty('--k', i + 1);
      ae.dataset.id = a.id; ae.dataset.key = a.key || '';
      const ai = document.createElement('img'); setImg(ai, a.key, 'small', a.name); ae.appendChild(ai);
      ae.title = a.name; ae.addEventListener('mouseenter', () => preview(a)); d.appendChild(ae);
    });
  }
  d.title = '';
  d.addEventListener('mouseenter', () => preview(ref));
  return d;
}
function backKey(key) { const c = CARDS[key]; return c && c.back && c.back.key ? c.back.key : key; }

function rowEl(label, refs, opts) {
  const r = document.createElement('div'); r.className = 'row ' + (opts.cls || '');
  if (label) { const l = document.createElement('div'); l.className = 'rowlbl'; l.textContent = label; r.appendChild(l); }
  if (!refs.length) { const e = document.createElement('div'); e.className = 'empty'; e.textContent = opts.empty || ''; r.appendChild(e); }
  refs.forEach((ref) => r.appendChild(cardEl(ref, Object.assign({enter: !prevIds.has(ref.id)}, opts, {attachments: (opts.attachmentsOf || {})[ref.id]}))));
  return r;
}

function pileEl(label, refs) {
  const p = document.createElement('div'); p.className = 'pile' + (refs.length ? '' : ' none');
  p.innerHTML = `<div class="pilelbl">${esc(label)}</div><div class="pilecount">${refs.length}</div>`;
  if (refs.length) {
    const top = refs[refs.length - 1];
    const img = document.createElement('img'); setImg(img, top.key, 'small', top.name); p.appendChild(img);
    p.addEventListener('click', (ev) => { ev.stopPropagation(); openPopover(label, refs); });
    p.addEventListener('mouseenter', () => preview(top));
  }
  return p;
}

function manaPips(s) { return (s || '').split('').map((c) => `<span class="pip ${c}">${c}</span>`).join(''); }

function playerPanel(side, p, f) {
  const el = $('panel' + side);
  el.dataset.player = side;
  const hit = prevLife[side] != null && p.life < prevLife[side];
  el.className = 'ppanel ' + (side === 'A' ? 'us' : 'them') + (f.active === side ? ' active' : '') + (f.priority === side ? ' prio' : '');
  el.innerHTML = `<div class="pname">${esc(side === 'A' ? META.playerA : META.playerB)}</div>
    <div class="life${hit ? ' hit' : ''}">${p.life ?? '–'}</div>
    <div class="pstats"><span title="library">📚 ${p.library ?? '?'}</span><span title="hand">✋ ${p.hand ? p.hand.length : (p.hand_count ?? '?')}</span></div>
    <div class="mana">${manaPips(p.mana_pool)}</div>
    ${Object.keys(p.counters || {}).length ? `<div class="pctr">${Object.entries(p.counters).map(([k, v]) => `${k} ${v}`).join(' · ')}</div>` : ''}
    <div class="marks">${f.active === side ? '<span class="mk act">active</span>' : ''}${f.priority === side ? '<span class="mk pr">priority</span>' : ''}</div>`;
}

function splitBoard(bf) {
  const byId = {}; bf.forEach((c) => byId[c.id] = c);
  const attachmentsOf = {};
  const top = bf.filter((c) => {
    if (c.attached_to && byId[c.attached_to]) { (attachmentsOf[c.attached_to] = attachmentsOf[c.attached_to] || []).push(c); return false; }
    return true;
  });
  const isLand = (c) => (c.types || (CARDS[c.key] || {}).types || []).includes('Land') && !(c.power != null);
  return {lands: top.filter(isLand), others: top.filter((c) => !isLand(c)), attachmentsOf};
}

function renderBoard(f, animate) {
  const b = f.board, A = b.players.A, B = b.players.B;
  playerPanel('B', B, f); playerPanel('A', A, f);
  const bf = $('battlefield'); bf.innerHTML = '';
  const sb = splitBoard(B.battlefield || []), sa = splitBoard(A.battlefield || []);
  const handB = B.hand ? B.hand : Array.from({length: B.hand_count || 0}, (_, i) => ({id: 'Bh' + i, name: 'hidden'}));
  bf.appendChild(rowEl('their hand', handB, {cls: 'hand them', hidden: HANDHIDE.B || !B.hand, empty: 'empty'}));
  bf.appendChild(rowEl('', sb.others, {cls: 'perm them', attachmentsOf: sb.attachmentsOf, empty: 'no permanents'}));
  bf.appendChild(rowEl('', sb.lands, {cls: 'lands them', attachmentsOf: sb.attachmentsOf, empty: ''}));
  const mid = document.createElement('div'); mid.className = 'midline'; bf.appendChild(mid);
  bf.appendChild(rowEl('', sa.lands, {cls: 'lands us', attachmentsOf: sa.attachmentsOf, empty: ''}));
  bf.appendChild(rowEl('', sa.others, {cls: 'perm us', attachmentsOf: sa.attachmentsOf, empty: 'no permanents'}));
  bf.appendChild(rowEl('our hand', A.hand || [], {cls: 'hand us', empty: 'empty'}));
  // piles
  const piles = $('piles'); piles.innerHTML = '';
  piles.appendChild(pileEl('their graveyard', B.graveyard || []));
  piles.appendChild(pileEl('their exile', B.exile || []));
  piles.appendChild(pileEl('our exile', A.exile || []));
  piles.appendChild(pileEl('our graveyard', A.graveyard || []));
  // stack
  const st = $('stack'); st.innerHTML = '<div class="zlbl">stack</div>';
  const items = (b.stack || []).slice().reverse();      // top of stack first
  if (!items.length) st.innerHTML += '<div class="empty">empty</div>';
  items.forEach((it, i) => {
    const d = document.createElement('div');
    d.className = 'sitem ' + (it.controller === 'A' ? 'us' : 'them') + (it.ability ? ' abil' : '') + (i === 0 ? ' top' : '');
    d.dataset.sid = it.id; d.dataset.targets = (it.targets || []).map((t) => t.id).join(',');
    const img = document.createElement('img'); setImg(img, it.key, 'small', it.source_name || it.name); d.appendChild(img);
    const t = document.createElement('div'); t.className = 'stext';
    const tg = (it.targets || []).map((x) => x.kind === 'player' ? (x.name === 'A' ? META.playerA : META.playerB) : x.name);
    t.innerHTML = `<div class="sname">${it.ability ? '<span class="abchip">ability</span> ' : ''}${esc(it.ability ? (it.source_name || it.name) : it.name)}${it.mana_cost && !it.ability ? ` <span class="cost">${esc(it.mana_cost)}</span>` : ''}</div>
      <div class="srules">${esc(it.rules || '')}</div>${tg.length ? `<div class="stg">→ ${esc(tg.join(', '))}</div>` : ''}`;
    d.appendChild(t);
    d.addEventListener('mouseenter', () => preview({key: it.key, name: it.name, rules_now: it.rules}));
    st.appendChild(d);
  });
  // phase bar
  $('turn').textContent = f.turn ? `Turn ${f.turn}` : 'Pre-game';
  $('who').textContent = f.active === 'A' ? `${META.playerA}'s turn` : f.active === 'B' ? `${META.playerB}'s turn` : '';
  $('who').className = 'who ' + (f.active === 'A' ? 'us' : 'them');
  $('steps').innerHTML = STEPS.filter((s) => s !== 'FCD').map((s) => `<span class="stp${f.step === s ? ' on' : ''}">${s}</span>`).join('');
  $('clock').textContent = `frame ${cur + 1}/${N}`;
  const chip = $('dchip'); chip.textContent = CHIPLBL[f.src] || f.src; chip.className = 'chip ' + f.src;
  // remember for diffs
  prevIds = new Set([...(A.battlefield || []), ...(B.battlefield || []), ...(A.hand || []), ...(B.hand || [])].map((c) => c.id));
  prevLife = {A: A.life, B: B.life};
  whenImagesReady($('board')).then(drawArrows);
  drawArrows();
}

// ---------- arrows ----------
function centerOf(el, base) {
  const r = el.getBoundingClientRect(), b = base.getBoundingClientRect();
  return {x: r.left - b.left + r.width / 2, y: r.top - b.top + r.height / 2, w: r.width, h: r.height};
}
function drawArrows() {
  const board = $('board'), svg = $('arrows');
  const bb = board.getBoundingClientRect();
  svg.setAttribute('viewBox', `0 0 ${bb.width} ${bb.height}`);
  svg.setAttribute('width', bb.width); svg.setAttribute('height', bb.height);
  const f = FRAMES[cur], b = f.board;
  let out = '';
  const find = (id) => board.querySelector(`[data-id="${CSS.escape(id)}"]`);
  const arrow = (from, to, cls) => {
    if (!from || !to) return;
    const a = centerOf(from, board), c = centerOf(to, board);
    const mx = (a.x + c.x) / 2, my = (a.y + c.y) / 2 - Math.abs(c.x - a.x) * 0.15 - 20;
    out += `<path class="arr ${cls}" d="M${a.x},${a.y} Q${mx},${my} ${c.x},${c.y}"/>`;
  };
  // stack -> targets
  (b.stack || []).forEach((it) => {
    const from = board.querySelector(`[data-sid="${CSS.escape(it.id)}"]`);
    (it.targets || []).forEach((t) => {
      const to = t.kind === 'player' ? $('panel' + t.name) : (find(t.id) || board.querySelector(`[data-sid="${CSS.escape(t.id)}"]`));
      arrow(from, to, 'tgt');
    });
  });
  // combat
  (b.combat || []).forEach((g) => {
    const def = g.defender_id ? find(g.defender_id) : $('panel' + g.defender);
    (g.attackers || []).forEach((aid) => {
      arrow(find(aid), def, 'atk');
      (g.blockers || []).forEach((bid) => arrow(find(bid), find(aid), 'blk'));
    });
  });
  svg.innerHTML = `<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>` + out;
}
function whenImagesReady(root, timeout) {
  const imgs = Array.from(root.querySelectorAll('img')).filter((i) => !i.complete);
  if (!imgs.length) return Promise.resolve();
  return new Promise((res) => {
    let n = imgs.length; const done = () => { if (--n <= 0) res(); };
    imgs.forEach((i) => { i.addEventListener('load', done, {once: true}); i.addEventListener('error', done, {once: true}); });
    setTimeout(res, timeout || 4000);
  });
}

// ---------- preview + popover ----------
function preview(ref) {
  const card = CARDS[ref.key] || {};
  const pv = $('preview');
  const img = pv.querySelector('img'); setImg(img, ref.key, 'normal', ref.name);
  const rules = ref.rules_now || (card.rules || []).join('\n');
  pv.querySelector('.pvtext').innerHTML = `<b>${esc(ref.name || card.name)}</b> <span class="cost">${esc(card.mana_cost || '')}</span>
    <div class="tl">${esc(card.type_line || '')}</div><div class="rl">${esc(rules)}</div>
    ${ref.counters ? `<div class="tl">counters: ${esc(Object.entries(ref.counters).map(([k, v]) => `${k} ×${v}`).join(', '))}</div>` : ''}`;
  pv.classList.add('on');
}
function openPopover(label, refs) {
  const po = $('popover'); po.innerHTML = `<div class="pohead">${esc(label)} (${refs.length}) <button id="poclose">×</button></div><div class="pogrid"></div>`;
  const g = po.querySelector('.pogrid'); refs.forEach((r) => g.appendChild(cardEl(r, {})));
  po.classList.add('on'); $('poclose').onclick = closePopover;
}
function closePopover() { $('popover').classList.remove('on'); }

// ---------- log ----------
function buildLog() {
  const log = $('log'); let html = '';
  FRAMES.forEach((f, i) => {
    (f.events || []).forEach((e) => {
      html += `<div class="ev" data-f="${i}" data-turn="${f.turn}">${e.text ? esc(e.text) : ''}</div>`;
    });
    if (f.decision && f.src !== 'auto' && f.src !== 'plan') {
      html += `<div class="ev dec ${f.src}" data-f="${i}">▸ ${esc(CHIPLBL[f.src] || f.src)}: ${esc(KINDLBL[f.kind] || f.kind || '')}${f.decision.why ? ' — ' + esc(f.decision.why.slice(0, 140)) : ''}</div>`;
    }
  });
  log.innerHTML = html;
  log.addEventListener('click', (ev) => { const t = ev.target.closest('.ev'); if (t) goto(+t.dataset.f, true); });
}
function updateLog() {
  const log = $('log');
  let last = null;
  log.querySelectorAll('.ev').forEach((el) => {
    const fi = +el.dataset.f;
    el.classList.toggle('future', fi > cur);
    el.classList.toggle('now', fi === cur);
    if (fi <= cur) last = el;
  });
  if (last) log.scrollTop = last.offsetTop - log.clientHeight + last.offsetHeight + 8;
}

// ---------- decision tree ----------
const collapsed = {};          // frameIndex -> Set(nodeId)
let view = {k: 1, x: 0, y: 0}; // pan/zoom
let selected = null;
const CH = 6.9, GAP = 26, ROWH = 30;

function visibleNodes(tree, fi) {
  const col = collapsed[fi] || new Set();
  const byId = {}; tree.nodes.forEach((n) => byId[n.id] = n);
  const hidden = new Set();
  tree.nodes.forEach((n) => { let p = n.parent; while (p != null) { if (col.has(p)) { hidden.add(n.id); break; } p = byId[p].parent; } });
  return tree.nodes.filter((n) => !hidden.has(n.id)).map((n) => Object.assign({}, n, {collapsed: col.has(n.id)}));
}
function subtreeStats(tree, id) {
  const byId = {}; tree.nodes.forEach((n) => byId[n.id] = n);
  let leaves = 0;
  tree.nodes.forEach((n) => { if (n.kind === 'leaf') { let p = n.parent; while (p != null) { if (p === id) { leaves++; break; } p = byId[p].parent; } } });
  return leaves;
}
function layoutTree(nodesIn, tree) {
  const nodes = nodesIn.map((n) => Object.assign({}, n, {children: []}));
  const byId = {}; nodes.forEach((n) => byId[n.id] = n);
  nodes.forEach((n) => { if (n.parent != null && byId[n.parent]) byId[n.parent].children.push(n); });
  const maxDepth = Math.max(...nodes.map((n) => n.depth));
  nodes.forEach((n) => { if (n.collapsed) n.pill = `+${subtreeStats(tree, n.id)} leaves`; });
  let y = 12;
  function place(n) {
    if (!n.children.length) { n.y = y + ROWH / 2; y += ROWH; return; }
    n.children.forEach(place);
    n.y = (n.children[0].y + n.children[n.children.length - 1].y) / 2;
  }
  place(byId[0]);
  const extra = (n) => n.kind === 'leaf' ? 92 : (n.kind === 'candidate' && n.agg != null ? 56 : 0) + (n.pill ? 80 : 0);
  const fixed = [], label = [];
  for (let d = 0; d <= maxDepth; d++) {
    const col = nodes.filter((n) => n.depth === d);
    label[d] = Math.min(44, Math.max(...col.map((n) => n.label.length))) * CH + 3;
    fixed[d] = 14 + Math.max(...col.map(extra)) + GAP;
  }
  const colW = fixed.map((f, d) => f + label[d]);
  const x0 = []; colW.reduce((acc, w, d) => { x0[d] = acc; return acc + w; }, 10);
  nodes.forEach((n) => {
    n.x = x0[n.depth];
    const maxW = colW[n.depth] - GAP;
    n.fit = Math.max(6, Math.floor((maxW - 14 - extra(n)) / CH + 0.1));
    n.text = n.label.length > n.fit ? n.label.slice(0, n.fit - 1) + '…' : n.label;
    n.w = n.kind === 'leaf' ? maxW : Math.min(maxW, 14 + n.text.length * CH + extra(n));
    n.h = 26;
  });
  const W = x0[maxDepth] + colW[maxDepth], H = y + 12;
  return {nodes, byId, W, H};
}
function scoreColor(s) {
  if (s == null) return 'var(--faint)';
  const t = Math.max(0, Math.min(1, s / 100));
  return `rgb(${Math.round(214 + (132 - 214) * t)},${Math.round(119 + (181 - 119) * t)},${Math.round(109 + (110 - 109) * t)})`;
}
let lastLayout = null;
function renderTree(f, animate) {
  const svg = $('tree'), g = $('pz');
  const tree = f.decision && f.decision.tree;
  $('treehint').hidden = !!tree;
  if (!tree) { g.innerHTML = ''; lastLayout = null; return; }
  const {nodes, byId, W, H} = layoutTree(visibleNodes(tree, cur), tree);
  lastLayout = {W, H};
  const chosenPath = new Set();
  tree.nodes.forEach((n) => { if (n.chosen) { let p = n; const all = {}; tree.nodes.forEach((m) => all[m.id] = m); while (p) { chosenPath.add(p.id); p = p.parent != null ? all[p.parent] : null; } } });
  const order = {}; let k = 0;
  nodes.slice().sort((a, b) => a.depth - b.depth || a.y - b.y).forEach((n) => order[n.id] = k++);
  const dt = animate ? Math.min(90, 2200 / Math.max(1, nodes.length)) : 0;
  let out = '';
  nodes.forEach((n) => {
    if (n.parent == null || !byId[n.parent]) return;
    const p = byId[n.parent];
    const x1 = p.x + p.w, y1 = p.y, x2 = n.x, y2 = n.y, mx = (x1 + x2) / 2;
    const cls = 'edge' + (chosenPath.has(n.id) && chosenPath.has(p.id) ? ' chosen' : '');
    out += `<path class="${cls}" d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}" style="animation-delay:${order[n.id] * dt}ms"></path>`;
  });
  nodes.forEach((n) => {
    const dim = tree.chosen != null && n.depth >= 1 && !chosenPath.has(n.id) && n.kind !== 'group';
    const cls = ['node', n.kind, n.chosen ? 'chosen' : '', dim ? 'dim' : '', selected === n.id ? 'sel' : '', n.collapsed ? 'col' : ''].join(' ');
    const ty = n.y + 4;
    let inner = `<rect x="${n.x}" y="${n.y - n.h / 2}" width="${n.w}" height="${n.h}" rx="5"></rect>`;
    if (n.kind === 'leaf') {
      const life = n.life ? `${n.life[0]}–${n.life[1]}` : '';
      inner += `<text x="${n.x + 7}" y="${ty}">${esc(n.text)}</text><text class="lifetxt" x="${n.x + n.w - 62}" y="${ty}">${esc(life)}</text>` +
        `<text class="score" x="${n.x + n.w - 26}" y="${ty}" style="fill:${scoreColor(n.score)}">${n.score ?? '–'}</text>`;
    } else {
      inner += `<text x="${n.x + 7}" y="${ty}">${esc(n.text)}</text>`;
      if (n.kind === 'candidate' && n.agg != null) inner += `<text class="agg" text-anchor="end" x="${n.x + n.w - (n.pill ? 86 : 6)}" y="${ty}" style="animation-delay:${order[n.id] * dt + 1200}ms">${n.agg}</text>`;
      if (n.pill) inner += `<text class="pill" text-anchor="end" x="${n.x + n.w - 6}" y="${ty}">${esc(n.pill)}</text>`;
    }
    out += `<g class="${cls}" data-node="${n.id}" style="animation-delay:${order[n.id] * dt}ms">${inner}</g>`;
  });
  g.innerHTML = out;
  svg.classList.toggle('anim', !!animate);
  g.querySelectorAll('.node').forEach((el) => {
    const id = +el.dataset.node, n = tree.nodes[id];
    el.addEventListener('click', (ev) => { ev.stopPropagation(); onNodeClick(n, tree); });
    el.addEventListener('mousemove', (ev) => showTip(ev, n));
    el.addEventListener('mouseleave', hideTip);
  });
  fitTree();
}
function onNodeClick(n, tree) {
  if (n.kind === 'candidate' || n.kind === 'branch' || n.kind === 'group') {
    const s = collapsed[cur] = collapsed[cur] || new Set();
    if (s.has(n.id)) s.delete(n.id); else if (tree.nodes.some((m) => m.parent === n.id)) s.add(n.id);
  }
  selected = n.id;
  renderTree(FRAMES[cur], false);
  renderDetail(FRAMES[cur], n, tree);
}
function showTip(ev, n) {
  const tip = $('tip');
  let html = `<b>${esc(n.full || n.label)}</b>`;
  if (n.kind === 'leaf') html += `<div>score <b style="color:${scoreColor(n.score)}">${n.score ?? '–'}</b>${n.heuristic != null ? ` · heuristic ${n.heuristic}` : ''}${n.life ? ` · life ${n.life[0]}–${n.life[1]}` : ''}</div>` +
    (n.our_board ? `<div class="tb">us: ${esc(n.our_board)}</div><div class="tb">them: ${esc(n.opp_board)}</div>` : '');
  if (n.kind === 'candidate' && n.agg != null) html += `<div>aggregate <b>${n.agg}</b> (${esc(n.rule || '')}) · ${n.n_leaves} leaves · click to ${(collapsed[cur] || new Set()).has(n.id) ? 'expand' : 'collapse'}</div>`;
  tip.innerHTML = html; tip.classList.add('on');
  const r = document.body.getBoundingClientRect();
  tip.style.left = Math.min(ev.clientX + 14, r.width - 360) + 'px';
  tip.style.top = (ev.clientY + 14) + 'px';
}
function hideTip() { $('tip').classList.remove('on'); }

// pan / zoom
function applyView() { $('pz').setAttribute('transform', `translate(${view.x},${view.y}) scale(${view.k})`); }
function fitTree() {
  const svg = $('tree'); const box = svg.getBoundingClientRect();
  if (!lastLayout) return;
  const k = Math.max(0.3, Math.min(PRESENT ? 1.5 : 1.25, (box.width - 20) / lastLayout.W, (box.height - 20) / lastLayout.H));
  view = {k, x: Math.max(10, (box.width - lastLayout.W * k) / 2), y: Math.max(10, (box.height - lastLayout.H * k) / 2)};
  applyView();
}
(function bindPanZoom() {
  const svg = $('tree'); let drag = null;
  svg.addEventListener('wheel', (ev) => {
    ev.preventDefault();
    const r = svg.getBoundingClientRect(), px = ev.clientX - r.left, py = ev.clientY - r.top;
    const f = ev.deltaY < 0 ? 1.12 : 1 / 1.12, k2 = Math.max(0.2, Math.min(4, view.k * f));
    view.x = px - (px - view.x) * (k2 / view.k); view.y = py - (py - view.y) * (k2 / view.k); view.k = k2; applyView();
  }, {passive: false});
  svg.addEventListener('mousedown', (ev) => { drag = {x: ev.clientX, y: ev.clientY, vx: view.x, vy: view.y}; svg.classList.add('drag'); });
  window.addEventListener('mousemove', (ev) => { if (drag) { view.x = drag.vx + ev.clientX - drag.x; view.y = drag.vy + ev.clientY - drag.y; applyView(); } });
  window.addEventListener('mouseup', () => { drag = null; svg.classList.remove('drag'); });
  svg.addEventListener('dblclick', fitTree);
})();

// ---------- detail panel ----------
function chips(s) { return (s || '').split(/[;,|]/).map((x) => x.trim()).filter(Boolean).map((x) => `<span class="chipx">${esc(x)}</span>`).join(''); }
function renderDetail(f, node, tree) {
  const d = $('detail'); const dec = f.decision;
  let html = '';
  if (node && node.kind === 'leaf') {
    html += `<div class="dh">simulated leaf</div><div class="dline">${esc(node.full || node.label)}</div>
      <div class="scorebar"><div style="width:${Math.max(0, Math.min(100, node.score || 0))}%;background:${scoreColor(node.score)}"></div><span>score ${node.score ?? '–'}${node.heuristic != null ? ` · heuristic ${node.heuristic}` : ''}</span></div>
      ${node.life ? `<div class="kv">life <b>${node.life[0]}</b> us · <b>${node.life[1]}</b> them${node.hand != null ? ` · hand ${node.hand}` : ''}</div>` : ''}
      ${node.our_board ? `<div class="kv">our board</div><div class="chips">${chips(node.our_board)}</div><div class="kv">their board</div><div class="chips">${chips(node.opp_board)}</div>` : ''}`;
  } else if (node && node.kind === 'candidate' && tree) {
    const leaves = tree.nodes.filter((n) => n.kind === 'leaf' && underNode(tree, n, node.id)).sort((a, b) => (b.score ?? -1) - (a.score ?? -1));
    html += `<div class="dh">candidate${node.chosen ? ' · chosen' : ''}</div><div class="dline">${esc(node.full || node.label)}</div>
      <div class="kv">aggregate <b>${node.agg ?? '–'}</b> ${node.rule ? `(${esc(node.rule)})` : ''} · ${leaves.length} leaves</div>` +
      leaves.map((l) => `<div class="scorebar small" data-leaf="${l.id}"><div style="width:${Math.max(0, Math.min(100, l.score || 0))}%;background:${scoreColor(l.score)}"></div><span>${l.score ?? '–'} · ${esc((l.full || l.label).replace(/^[^|]*\|\s*/, '').slice(0, 70))}</span></div>`).join('');
  }
  if (dec) {
    const kl = KINDLBL[f.kind] || f.kind || '';
    html += `<div class="dh">${esc(CHIPLBL[f.src] || f.src)}${kl && kl !== (CHIPLBL[f.src] || '').toLowerCase() ? ' · ' + esc(kl) : ''}${dec.decision ? ' · ' + esc(dec.decision) : ''}${dec.leaf_count ? ` · ${dec.leaf_count} leaves` : ''}</div>`;
    if (dec.why) html += `<div class="why">${esc(dec.why)}</div>`;
    if (dec.plan) html += `<div class="plan"><b>plan</b> ${esc(dec.plan)}</div>`;
    if (dec.note) html += `<div class="plan"><b>plan step</b> ${esc(dec.note)}</div>`;
    if (dec.chosen_line) html += `<div class="plan"><b>line</b> ${esc(typeof dec.chosen_line === 'string' ? dec.chosen_line : dec.chosen_line.label || JSON.stringify(dec.chosen_line))}</div>`;
    if (dec.options && dec.options.length) {
      const picked = dec.response && dec.response.choice;
      html += `<div class="options">${dec.options.map((o) => `<div class="opt${o.index === picked ? ' picked' : ''}"><span class="oi">${o.index}</span>${esc(o.text || '')}</div>`).join('')}</div>`;
    }
    if (dec.response) html += `<div class="answer">${esc(JSON.stringify(dec.response)).slice(0, 300)}</div>`;
  } else if (f.events && f.events.length) {
    html += `<div class="dh">game log</div>` + f.events.map((e) => `<div class="evd">${esc(e.text)}</div>`).join('');
  } else {
    html += `<div class="dh">${esc(CHIPLBL[f.src] || '')}</div>`;
  }
  d.innerHTML = html;
  d.querySelectorAll('[data-leaf]').forEach((el) => el.addEventListener('click', () => { const l = tree.nodes[+el.dataset.leaf]; selected = l.id; renderTree(f, false); renderDetail(f, l, tree); }));
}
function underNode(tree, n, id) { let p = n.parent; while (p != null) { if (p === id) return true; p = tree.nodes[p].parent; } return false; }

// ---------- timeline ----------
function buildTimeline() {
  const tl = $('timeline'); const items = META.timeline || [];
  const W = 1000;
  let html = `<svg viewBox="0 0 ${W} 22" preserveAspectRatio="none">`;
  let lastTurn = null;
  FRAMES.forEach((f, i) => { if (f.turn !== lastTurn && f.turn) { const x = (i / Math.max(1, N - 1)) * W; html += `<line x1="${x}" y1="0" x2="${x}" y2="22" class="tk"/><text x="${x + 2}" y="8" class="tt">${f.turn}</text>`; lastTurn = f.turn; } });
  html += '</svg>';
  items.forEach((it) => {
    const x = (it.i / Math.max(1, N - 1)) * 100;
    const r = it.src === 'search' || it.src === 'planning' ? 6 : it.src === 'pilot' ? 5 : 3;
    html += `<div class="dot ${it.src}" data-f="${it.i}" style="left:${x}%;width:${r * 2}px;height:${r * 2}px;margin-left:-${r}px;${it.agg != null ? `background:${scoreColor(it.agg)};` : ''}" title="${esc(`T${it.turn} ${it.src}${it.agg != null ? ' agg ' + it.agg : ''}`)}"></div>`;
  });
  html += `<div class="cursor" id="tlcur"></div>`;
  tl.innerHTML = html;
  tl.addEventListener('click', (ev) => {
    const dot = ev.target.closest('.dot');
    if (dot) { goto(+dot.dataset.f, true); return; }
    const r = tl.getBoundingClientRect(); goto(Math.round((ev.clientX - r.left) / r.width * (N - 1)), true);
  });
}
function updateTimeline() { $('tlcur').style.left = (cur / Math.max(1, N - 1) * 100) + '%'; }

// ---------- transport ----------
let cur = 0, playing = false, timer = null;
function render(animate) {
  const f = FRAMES[cur];
  closePopover(); hideTip(); selected = null;
  renderBoard(f, animate);
  $('dtitle').textContent = (KINDLBL[f.kind] || f.kind || (f.src === 'event' ? 'game log' : '')).toUpperCase() +
    (f.decision && f.decision.decision ? `: ${f.decision.decision.toUpperCase()}` : '') + (f.decision && f.decision.leaf_count ? ` (${f.decision.leaf_count} simulated leaves)` : '');
  renderTree(f, animate);
  renderDetail(f, null, f.decision && f.decision.tree);
  updateLog(); updateTimeline();
  $('scrub').value = cur; $('pos').textContent = `${cur + 1} / ${N}`;
}
function frameDuration(i) { const f = FRAMES[i ?? cur]; return (f.dur || 1500) / parseFloat($('speed').value || '1'); }
function skippable(i) { const f = FRAMES[i]; return (f.src === 'auto' && $('skipauto').checked) || (f.src === 'event' && $('skipev').checked); }
function nextIndex(i) { let j = i + 1; while (j < N && skippable(j)) j++; return j < N ? j : null; }
function goto(i, animate) { cur = Math.max(0, Math.min(N - 1, i)); render(animate !== false); }
function next() { const j = nextIndex(cur); if (j == null) return null; goto(j, true); return j; }
function prevDecision() { for (let j = cur - 1; j >= 0; j--) if (FRAMES[j].decision && !['auto', 'plan'].includes(FRAMES[j].src)) { goto(j, true); return; } }
function nextDecision() { for (let j = cur + 1; j < N; j++) if (FRAMES[j].decision && !['auto', 'plan'].includes(FRAMES[j].src)) { goto(j, true); return; } }
function tick() { if (!playing) return; const j = next(); if (j == null) { setPlaying(false); return; } timer = setTimeout(tick, frameDuration()); }
function setPlaying(p) { playing = p; $('play').textContent = p ? '❚❚' : '▶'; clearTimeout(timer); if (p) timer = setTimeout(tick, frameDuration()); }

$('play').onclick = () => setPlaying(!playing);
$('restart').onclick = () => { setPlaying(false); goto(0, true); };
$('stepb').onclick = () => { setPlaying(false); goto(cur - 1, false); };
$('stepf').onclick = () => { setPlaying(false); goto(cur + 1, true); };
$('scrub').max = N - 1; $('scrub').oninput = (e) => { setPlaying(false); goto(+e.target.value, false); };
$('hideB').onchange = (e) => { HANDHIDE.B = e.target.checked; render(false); };
document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if (e.key === ' ') { e.preventDefault(); setPlaying(!playing); }
  else if (e.key === 'ArrowRight') { setPlaying(false); goto(cur + 1, true); }
  else if (e.key === 'ArrowLeft') { setPlaying(false); goto(cur - 1, false); }
  else if (e.key === ']') { setPlaying(false); nextDecision(); }
  else if (e.key === '[') { setPlaying(false); prevDecision(); }
  else if (e.key === 'f') fitTree();
  else if (e.key === '+' || e.key === '=') { view.k *= 1.15; applyView(); }
  else if (e.key === '-') { view.k /= 1.15; applyView(); }
  else if (e.key === 'e') { $('skipev').checked = !$('skipev').checked; }
  else if (e.key === 'h') { $('hideB').checked = !$('hideB').checked; HANDHIDE.B = $('hideB').checked; render(false); }
  else if (e.key === 'Escape') { closePopover(); hideTip(); }
});
document.addEventListener('click', (e) => { if (!e.target.closest('#popover') && !e.target.closest('.pile')) closePopover(); });
window.addEventListener('resize', () => { drawArrows(); fitTree(); });

buildLog(); buildTimeline();
goto(0, true);

window.__replay = {
  get total() { return N; },
  index: () => cur,
  goto: (i, animate) => { setPlaying(false); goto(i, animate); },
  next: () => { setPlaying(false); return next(); },
  duration: (i) => frameDuration(i),
  frame: (i) => { const f = FRAMES[i ?? cur]; return {turn: f.turn, phase: f.phase, step: f.step, src: f.src, kind: f.kind, snap: f.snap}; },
  ready: () => whenImagesReady($('board'), 4000),
  fit: fitTree,
};
})();
