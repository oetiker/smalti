/* Smalti specimen site.
 *
 * Everything on this page comes out of data/glyphs.json, which `make site`
 * writes straight from the glyph store.  Nothing about the font is restated
 * here, because a restatement is a second source of truth and would go stale.
 *
 * The one rule worth knowing before changing anything: the text this page can
 * put on a contributor's clipboard has to be BYTE-IDENTICAL to the .txt file
 * the repository holds, or a pull request made from it shows a spurious diff.
 * That is why the header line is shipped verbatim in the JSON rather than
 * rebuilt here -- see fileText().
 */
'use strict';

var D = null;              // the whole data file
var NAME = [];             // per listed codepoint: its Unicode name
var SHOWN = [];            // per listed codepoint: the character, or ''
var COVI = null;           // listed index -> index into bits/layers, or -1
var FACE = 'regular';
var ZOOM = 2;
var FILT = 'all';
var QUERY = '';

var HEAD_RE = /^# U\+([0-9A-F]+) (.{3})  ([\s\S]*)$/;
var LAYER_NAME = {
  h: 'drawn by hand in this repository',
  u: 'upstream Tamzen, drawn by Scott Fial',
  g: 'computed by a generator'
};
var LAYER_SHORT = { h: 'drawn here', u: 'upstream', g: 'generated' };

function $(sel, root) { return (root || document).querySelector(sel); }
function el(tag, cls, text) {
  var n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
function hex(cp) { return cp.toString(16).toUpperCase().padStart(4, '0'); }
function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;');
}

/* ------------------------------------------------------------- glyph art -- */

/* One glyph as h strings of w characters.  k indexes the covered glyphs, which
 * are the listed codepoints whose state is '#', in the same order. */
function rowsOf(face, k) {
  var w = D.cell.w, h = D.cell.h, s = D.bits[face], off = k * h * 2, out = [];
  for (var y = 0; y < h; y++) {
    var v = parseInt(s.substr(off + y * 2, 2), 16), r = '';
    for (var x = 0; x < w; x++) r += (v >> (w - 1 - x)) & 1 ? '#' : '.';
    out.push(r);
  }
  return out;
}

function blankRows() {
  var r = [], i;
  for (i = 0; i < D.cell.h; i++) r.push('.'.repeat(D.cell.w));
  return r;
}

/* The exact bytes of glyphs/<size>/<face>/<CP>.txt.  The header line is taken
 * from the data file untouched: `make headers` decides its shape and this page
 * must not have an opinion about it. */
function fileText(i, rows) {
  return D.headers[i] + '\n' + rows.join('\n') + '\n';
}

/* A pixel drawing as inline SVG, for the sixteen codepoints a browser will not
 * render as text however good the font is: control codes and the soft hyphen
 * are not characters you can put in a span. */
function artSvg(rows, px) {
  var w = D.cell.w, h = D.cell.h, r = '', y, x;
  for (y = 0; y < h; y++) {
    for (x = 0; x < w; x++) {
      if (rows[y][x] === '#') r += '<rect x="' + x + '" y="' + y + '" width="1" height="1"/>';
    }
  }
  return '<svg class="art" width="' + (w * px / h) + '" height="' + px +
         '" viewBox="0 0 ' + w + ' ' + h + '" shape-rendering="crispEdges" ' +
         'fill="currentColor" aria-hidden="true">' + r + '</svg>';
}

/* --------------------------------------------------------------- startup -- */

function boot(data) {
  D = data;
  var i;
  COVI = new Int32Array(D.cps.length);
  var k = 0;
  for (i = 0; i < D.cps.length; i++) COVI[i] = D.state[i] === '#' ? k++ : -1;
  for (i = 0; i < D.headers.length; i++) {
    var m = HEAD_RE.exec(D.headers[i]);
    SHOWN.push(m ? m[2].trim() : '');
    NAME.push(m ? m[3] : '');
  }
  buildSpecimens();
  buildProvenance();
  buildBlocks();
  buildControls();
  renderGrid();
  window.addEventListener('hashchange', route);
  route();
  animateWordmark();
}

/* The tesserae are set left to right, the way a mosaicist lays them.  Done
 * here rather than in the SVG so a build stays free of per-tile inline style. */
function animateWordmark() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var tiles = document.querySelectorAll('.wordmark rect');
  var box = $('.wordmark');
  if (!box) return;
  var cols = box.viewBox.baseVal.width || 1;
  for (var i = 0; i < tiles.length; i++) {
    var x = parseFloat(tiles[i].getAttribute('x'));
    tiles[i].style.setProperty('--i', Math.round(x / cols * 46));
  }
}

/* ------------------------------------------------------------- specimens -- */

function buildSpecimens() {
  var host = $('#specimen-faces');
  D.faces.forEach(function (f) {
    var card = el('div', 'spec');
    var name = el('p', 'spec-name px');
    name.innerHTML = esc(D.faceLabel[f]) + ' <span>' + esc(D.faceFile[f]) + '</span>';
    card.appendChild(name);
    D.specimen.forEach(function (s) {
      var line = el('p', 'spec-line px s' + s.px + ' ' + faceClass(f));
      line.innerHTML = '<b>' + s.px + 'px</b>' + esc(s.text);
      card.appendChild(line);
    });
    host.appendChild(card);
  });
}

function faceClass(f) {
  return (f.indexOf('bold') === 0 ? 'bold ' : '') +
         (f.indexOf('italic') >= 0 ? 'oblique' : '');
}

/* ------------------------------------------------------------ provenance -- */

function buildProvenance() {
  var host = $('#provenance');
  var wrap = el('div', 'prov');
  D.totals.forEach(function (t) {
    var row = el('div', 'prov-row');
    row.appendChild(el('div', 'prov-name px', t.label));
    var bar = el('div', 'prov-bar');
    [['h', t.hand], ['u', t.upstream], ['g', t.gen]].forEach(function (p) {
      if (!p[1]) return;
      var s = el('span', p[0]);
      s.style.flex = p[1];
      s.title = p[1] + ' ' + LAYER_SHORT[p[0]];
      bar.appendChild(s);
    });
    /* The columns are a CSS rule, not an inline style: an inline width here
     * would outrank the narrow-screen media query and squeeze the bar to
     * nothing on a phone. */
    var n = el('div', 'prov-n px',
               t.hand + ' / ' + t.upstream + ' / ' + t.gen + '  = ' + t.total);
    row.appendChild(bar);
    row.appendChild(n);
    wrap.appendChild(row);
  });
  host.appendChild(wrap);
  var key = el('ul', 'prov-key px');
  ['h', 'u', 'g'].forEach(function (c) {
    var li = el('li');
    var i = el('i');
    i.style.background = c === 'h' ? 'var(--gold)'
                       : c === 'u' ? 'var(--cobalt)' : 'var(--verdigris)';
    li.appendChild(i);
    li.appendChild(document.createTextNode(LAYER_NAME[c]));
    key.appendChild(li);
  });
  host.appendChild(key);
}

/* ---------------------------------------------------------------- blocks -- */

function buildBlocks() {
  var legend = $('#cov-legend');
  legend.innerHTML =
    '<span><i class="on"></i>a glyph this font has</span>' +
    '<span><i class="off"></i>nobody has drawn it yet</span>' +
    '<span><i class="rule"></i>left undrawn by rule, East Asian Wide</span>';

  var host = $('#blocks'), wrap = el('div', 'blocks'), zero = [];
  D.blocks.forEach(function (b) {
    if (b.covered || b.extra) wrap.appendChild(blockRow(b));
    else zero.push(b);
  });
  host.appendChild(wrap);

  var note = $('#untouched-note');
  var total = zero.reduce(function (a, b) { return a + b.target; }, 0);
  note.textContent = zero.length + ' more Unicode blocks in the Basic ' +
    'Multilingual Plane have nothing drawn at all — ' + total.toLocaleString() +
    ' codepoints, and every one of them is somebody’s first pull request. ';
  var more = el('button', 'blk-more', 'Show the untouched blocks');
  more.addEventListener('click', function () {
    more.remove();
    var w2 = el('div', 'blocks');
    zero.forEach(function (b) { w2.appendChild(blockRow(b)); });
    note.parentNode.insertBefore(w2, note.nextSibling);
  });
  note.appendChild(more);
}

function blockRow(b) {
  var row = el('div', 'blk');
  var full = b.target > 0 && b.covered === b.target;
  if (full) row.className += ' full';
  if (!b.covered && !b.extra) row.className += ' zero';

  var nm = el('div', 'blk-name px');
  nm.appendChild(document.createTextNode(b.name));
  nm.appendChild(el('em', null, 'U+' + hex(b.start) + '..U+' + hex(b.end)));
  row.appendChild(nm);

  var n = el('div', 'blk-n px');
  n.innerHTML = '<b>' + b.covered + '</b>/' + b.target +
    (b.extra ? '<em style="display:block;font-style:normal">+' + b.extra + ' extra</em>' : '') +
    (b.byRule ? '<em style="display:block;font-style:normal;opacity:.7">' +
                b.byRule + ' by rule</em>' : '');
  row.appendChild(n);

  var strip = el('div', 'strip');
  if (b.to > b.from) {
    for (var i = b.from; i < b.to; i++) {
      var st = D.state[i];
      if (st === 'w') {
        var t = el('i', 'rule');
        t.title = 'U+' + hex(D.cps[i]) + ' ' + NAME[i] +
                  ' — East Asian Wide, taken from the emoji font';
        strip.appendChild(t);
      } else {
        var btn = el('button', st === '#' ? 'on' : 'off');
        btn.type = 'button';
        btn.dataset.i = i;
        btn.title = 'U+' + hex(D.cps[i]) + ' ' + NAME[i] +
                    (st === '#' ? '' : ' — not drawn yet');
        btn.setAttribute('aria-label', btn.title);
        btn.addEventListener('click', function (e) {
          openEditor(+e.currentTarget.dataset.i);
        });
        strip.appendChild(btn);
      }
    }
  } else {
    strip.appendChild(el('span', 'px', '—'));
    strip.firstChild.style.color = 'var(--grout2)';
  }
  row.appendChild(strip);
  return row;
}

/* ------------------------------------------------------------ the browser -- */

function buildControls() {
  var sel = $('#face');
  D.faces.forEach(function (f) {
    var o = el('option', null, D.faceLabel[f]);
    o.value = f;
    sel.appendChild(o);
  });
  sel.value = FACE;
  sel.addEventListener('change', function () { FACE = sel.value; renderGrid(); });

  Array.prototype.forEach.call(document.querySelectorAll('[name=zoom]'), function (r) {
    r.addEventListener('change', function () { ZOOM = +r.value; renderGrid(); });
  });
  Array.prototype.forEach.call(document.querySelectorAll('[name=filt]'), function (r) {
    r.addEventListener('change', function () { FILT = r.value; renderGrid(); });
  });
  var find = $('#find'), timer = null;
  find.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () {
      QUERY = find.value.trim().toLowerCase();
      renderGrid();
    }, 120);
  });
}

function matches(i) {
  var st = D.state[i];
  if (FILT === 'hand' && !(st === '#' && D.layers[FACE][COVI[i]] === 'h')) return false;
  if (FILT === 'gap' && st !== '.') return false;
  if (!QUERY) return true;
  if (NAME[i].toLowerCase().indexOf(QUERY) >= 0) return true;
  if (hex(D.cps[i]).toLowerCase().indexOf(QUERY) >= 0) return true;
  return SHOWN[i] !== '' && SHOWN[i] === QUERY;
}

function renderGrid() {
  var host = $('#grid');
  var px = ZOOM * D.cell.h;
  host.style.setProperty('--tsize', px + 'px');
  host.style.setProperty('--tile', (px + 2 * ZOOM + 12) + 'px');
  var html = '', shown = 0;

  D.blocks.forEach(function (b) {
    if (b.to <= b.from) return;
    var tiles = '', n = 0;
    for (var i = b.from; i < b.to; i++) {
      if (!matches(i)) continue;
      n++;
      tiles += tileHtml(i, px);
    }
    if (!n) return;
    shown += n;
    html += '<div class="blockhead"><h3>' + esc(b.name) + '</h3>' +
            '<span>U+' + hex(b.start) + '..U+' + hex(b.end) + ' &middot; ' +
            n + ' shown</span></div><div class="tiles">' + tiles + '</div>';
  });

  host.innerHTML = html || '<p class="empty prose">Nothing matches that. ' +
    'Try a Unicode name, a hex codepoint like 2192, or paste the character.</p>';
  $('#count').textContent = shown + ' of ' + D.cps.length +
    ' codepoints · ' + D.faceLabel[FACE] + ' · ' + px + 'px';
}

/* One listener for the whole grid rather than one per tile: the grid is
 * rebuilt on every change of face, size or filter, and 2263 listeners would
 * be rebuilt with it. */
$('#grid').addEventListener('click', function (e) {
  var t = e.target.closest('.tile[data-i]');
  if (t) openEditor(+t.dataset.i);
});

function tileHtml(i, px) {
  var cp = D.cps[i], st = D.state[i];
  var label = 'U+' + hex(cp) + ' ' + NAME[i];
  if (st === 'w') {
    return '<span class="tile rule" title="' + esc(label) +
           ' — East Asian Wide, taken from the emoji font">&#183;</span>';
  }
  if (st === '.') {
    return '<button class="tile miss" data-i="' + i + '" title="' + esc(label) +
           ' — not drawn yet, click to draw it" aria-label="' + esc(label) +
           ', not drawn yet">+</button>';
  }
  var layer = D.layers[FACE][COVI[i]];
  var body;
  if (D.textok[i] === '1') {
    body = '<b>' + esc(String.fromCodePoint(cp)) + '</b>';
  } else {
    body = artSvg(rowsOf(FACE, COVI[i]), px);
  }
  return '<button class="tile ' + layer + ' ' + faceClass(FACE) +
         '" data-i="' + i + '" title="' + esc(label) + ' — ' +
         LAYER_SHORT[layer] + '" aria-label="' + esc(label) + '">' + body +
         '</button>';
}

/* ---------------------------------------------------------------- editor -- */

var ED = null;    // {i, face, rows, orig}
var LAST_FOCUS = null;

function route() {
  var m = /^#\/glyph\/([a-z-]+)\/([0-9A-F]+)$/.exec(location.hash);
  if (!m) { if (ED) closeEditor(true); return; }
  var face = D.faces.indexOf(m[1]) >= 0 ? m[1] : 'regular';
  var cp = parseInt(m[2], 16);
  var i = D.cps.indexOf(cp);
  if (i < 0) { closeEditor(true); return; }
  if (ED && ED.i === i && ED.face === face) return;
  openEditor(i, face, true);
}

function openEditor(i, face, fromHash) {
  face = face || FACE;
  if (!fromHash) LAST_FOCUS = document.activeElement;
  var k = COVI[i];
  ED = {
    i: i, face: face,
    rows: k >= 0 ? rowsOf(face, k) : blankRows(),
    orig: k >= 0 ? rowsOf(face, k) : blankRows(),
    exists: k >= 0 && D.layers[face][k] === 'h'
  };
  drawEditor();
  $('#editor').hidden = false;
  $('#scrim').hidden = false;
  /* The drawer says aria-modal, so the page behind it has to actually stop
   * taking focus and stop being read out.  `inert` is the one line that does
   * both; a hand-rolled tab trap does neither for a screen reader. */
  $('main').inert = true;
  $('.masthead').inert = true;
  document.body.style.overflow = 'hidden';
  var want = '#/glyph/' + face + '/' + hex(D.cps[i]);
  if (location.hash !== want) history.replaceState(null, '', want);
  var first = $('.pix', $('#editor'));
  if (first) first.focus();
}

function closeEditor(silent) {
  ED = null;
  $('#editor').hidden = true;
  $('#editor').innerHTML = '';
  $('#scrim').hidden = true;
  $('main').inert = false;
  $('.masthead').inert = false;
  document.body.style.overflow = '';
  if (!silent && location.hash.indexOf('#/glyph/') === 0) {
    history.replaceState(null, '', location.pathname + location.search + '#browse');
  }
  if (LAST_FOCUS && LAST_FOCUS.isConnected) LAST_FOCUS.focus();
}

function drawEditor() {
  var host = $('#editor'), i = ED.i, cp = D.cps[i], k = COVI[i];
  var layer = k >= 0 ? D.layers[ED.face][k] : null;
  host.innerHTML = '';

  var top = el('div', 'ed-top');
  var h = el('h2', 'ed-title');
  h.id = 'ed-title';
  h.innerHTML = '<b>' + (D.textok[i] === '1' && SHOWN[i]
                          ? esc(SHOWN[i]) : '&nbsp;') + '</b>' + esc(NAME[i]);
  var sub = el('p', 'ed-sub', 'U+' + hex(cp) + '  ·  ' +
    (layer ? LAYER_NAME[layer] : 'not drawn yet'));
  var box = el('div');
  box.appendChild(h);
  box.appendChild(sub);
  top.appendChild(box);
  var close = el('button', 'ed-close', 'close ✕');
  close.addEventListener('click', function () { closeEditor(); });
  top.appendChild(close);
  host.appendChild(top);

  var faceRow = el('p', 'ed-sub');
  faceRow.style.margin = '14px 0 0';
  faceRow.appendChild(document.createTextNode('face  '));
  var fs = el('select');
  fs.className = 'px';
  fs.style.cssText = 'background:var(--mortar);color:var(--ink);' +
    'border:1px solid var(--grout2);padding:3px 7px;font-family:inherit;font-size:14px';
  D.faces.forEach(function (f) {
    var o = el('option', null, D.faceLabel[f]);
    o.value = f;
    fs.appendChild(o);
  });
  fs.value = ED.face;
  fs.addEventListener('change', function () { openEditor(ED.i, fs.value); });
  faceRow.appendChild(fs);
  host.appendChild(faceRow);

  var body = el('div', 'ed-body');
  body.appendChild(paintGrid());
  body.appendChild(sidePanel());
  host.appendChild(body);

  var help = el('p', 'ed-help');
  help.innerHTML = 'Click or drag to paint. Arrow keys move, space toggles. ' +
    'Rows and columns follow the grid the rest of the font uses: columns 0 ' +
    'and 6 are the side bearings, row 10 is the last row on the baseline, ' +
    'capitals start at row 3, x-height at row 5, and the maths axis is row 7.';
  host.appendChild(help);

  refresh();
}

var BASE = 10, CAP = 3, XH = 5, AXIS = 7;

function paintGrid() {
  var g = el('div', 'paint');
  g.setAttribute('role', 'group');
  g.setAttribute('aria-label', D.cell.w + ' by ' + D.cell.h + ' pixel grid');
  var painting = null;
  for (var y = 0; y < D.cell.h; y++) {
    for (var x = 0; x < D.cell.w; x++) {
      var b = el('button', 'pix');
      b.type = 'button';
      b.dataset.x = x;
      b.dataset.y = y;
      b.tabIndex = (x === 0 && y === 0) ? 0 : -1;
      b.setAttribute('role', 'checkbox');
      b.setAttribute('aria-label', 'column ' + x + ', row ' + y);
      if (x === 0 || x === D.cell.w - 1) b.className += ' side';
      if (y === BASE) b.className += ' base';
      if (y === CAP) b.className += ' cap';
      if (y === XH) b.className += ' xh';
      if (y === AXIS) b.className += ' axis';
      g.appendChild(b);
    }
  }
  g.addEventListener('pointerdown', function (e) {
    var t = e.target.closest('.pix');
    if (!t) return;
    e.preventDefault();
    painting = ED.rows[+t.dataset.y][+t.dataset.x] === '#' ? '.' : '#';
    setPixel(+t.dataset.x, +t.dataset.y, painting);
    t.focus();
    g.setPointerCapture(e.pointerId);
  });
  g.addEventListener('pointermove', function (e) {
    if (painting === null) return;
    var t = document.elementFromPoint(e.clientX, e.clientY);
    t = t && t.closest ? t.closest('.pix') : null;
    if (t && g.contains(t)) setPixel(+t.dataset.x, +t.dataset.y, painting);
  });
  window.addEventListener('pointerup', function () { painting = null; });
  g.addEventListener('keydown', onGridKey);
  return g;
}

function onGridKey(e) {
  var t = e.target.closest('.pix');
  if (!t) return;
  var x = +t.dataset.x, y = +t.dataset.y, w = D.cell.w, h = D.cell.h;
  var dx = { ArrowLeft: -1, ArrowRight: 1 }[e.key] || 0;
  var dy = { ArrowUp: -1, ArrowDown: 1 }[e.key] || 0;
  if (dx || dy) {
    e.preventDefault();
    var nx = Math.min(w - 1, Math.max(0, x + dx));
    var ny = Math.min(h - 1, Math.max(0, y + dy));
    var next = e.currentTarget.children[ny * w + nx];
    t.tabIndex = -1;
    next.tabIndex = 0;
    next.focus();
  } else if (e.key === ' ' || e.key === 'Enter') {
    e.preventDefault();
    setPixel(x, y, ED.rows[y][x] === '#' ? '.' : '#');
  }
}

function setPixel(x, y, v) {
  if (ED.rows[y][x] === v) return;
  ED.rows[y] = ED.rows[y].substring(0, x) + v + ED.rows[y].substring(x + 1);
  refresh();
}

function sidePanel() {
  var side = el('div', 'ed-side');

  var prev = el('div', 'ed-preview');
  [1, 2, 3].forEach(function (z) {
    var wrap = el('div');
    var c = el('canvas');
    c.width = D.cell.w * z;
    c.height = D.cell.h * z;
    c.className = 'prev' + z;
    c.setAttribute('aria-hidden', 'true');
    wrap.appendChild(c);
    var lab = el('div', 'px');
    lab.style.color = 'var(--ink-dim)';
    lab.textContent = z + '× ' + (z * D.cell.h) + 'px';
    wrap.appendChild(lab);
    prev.appendChild(wrap);
  });
  side.appendChild(prev);

  var geom = el('ul', 'ed-geom');
  [['var(--gold)', 'baseline, under row ' + BASE],
   ['var(--cobalt)', 'cap height at row ' + CAP + ', x-height at row ' + XH],
   ['var(--verdigris)', 'maths axis through row ' + AXIS]].forEach(function (p) {
    var li = el('li');
    var i = el('i');
    i.style.background = p[0];
    li.appendChild(i);
    li.appendChild(document.createTextNode(p[1]));
    geom.appendChild(li);
  });
  side.appendChild(geom);

  var path = el('p', 'ed-path');
  path.id = 'ed-path';
  side.appendChild(path);

  var ta = el('textarea', 'ed-file');
  ta.id = 'ed-file';
  ta.readOnly = true;
  ta.rows = D.cell.h + 2;
  ta.spellcheck = false;
  ta.setAttribute('aria-label', 'the text file for this glyph');
  side.appendChild(ta);

  var acts = el('div', 'ed-acts');
  var copy = el('button', 'primary', 'Copy the file');
  copy.type = 'button';
  copy.addEventListener('click', function () { copyFile(copy); });
  acts.appendChild(copy);

  var reset = el('button', null, 'Reset');
  reset.type = 'button';
  reset.id = 'ed-reset';
  reset.addEventListener('click', function () {
    ED.rows = ED.orig.slice();
    refresh();
  });
  acts.appendChild(reset);

  var gh = el('a', null, '');
  gh.id = 'ed-gh';
  gh.target = '_blank';
  gh.rel = 'noopener';
  acts.appendChild(gh);
  side.appendChild(acts);

  var hint = el('p', 'ed-help');
  hint.id = 'ed-hint';
  side.appendChild(hint);
  return side;
}

function copyFile(btn) {
  var text = fileText(ED.i, ED.rows);
  var done = function () {
    btn.textContent = 'Copied';
    setTimeout(function () { btn.textContent = 'Copy the file'; }, 1400);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, function () { select(); });
  } else {
    select();
  }
  function select() {
    var ta = $('#ed-file');
    ta.focus();
    ta.select();
    btn.textContent = 'Press ⌘C / Ctrl-C';
  }
}

/* Redraw everything that depends on the pixels: the grid, the previews, the
 * file text and the GitHub link. */
function refresh() {
  var host = $('#editor');
  var pix = host.querySelectorAll('.pix');
  for (var n = 0; n < pix.length; n++) {
    var x = +pix[n].dataset.x, y = +pix[n].dataset.y;
    var on = ED.rows[y][x] === '#';
    pix[n].classList.toggle('on', on);
    pix[n].setAttribute('aria-checked', on ? 'true' : 'false');
  }
  [1, 2, 3].forEach(function (z) {
    var c = $('.prev' + z, host);
    if (!c) return;
    var g = c.getContext('2d');
    g.fillStyle = '#1e1b15';
    g.fillRect(0, 0, c.width, c.height);
    g.fillStyle = '#efe7d3';
    for (var y = 0; y < D.cell.h; y++) {
      for (var x = 0; x < D.cell.w; x++) {
        if (ED.rows[y][x] === '#') g.fillRect(x * z, y * z, z, z);
      }
    }
  });

  var text = fileText(ED.i, ED.rows);
  $('#ed-file').value = text;
  var rel = 'glyphs/' + D.size + '/' + ED.face + '/' + hex(D.cps[ED.i]) + '.txt';
  $('#ed-path').innerHTML = 'the file is <b>' + esc(rel) + '</b>';
  $('#ed-reset').disabled = text === fileText(ED.i, ED.orig);

  var gh = $('#ed-gh'), hint = $('#ed-hint');
  if (!D.repo) {
    gh.hidden = true;
    hint.textContent = 'This build does not know which GitHub repository it ' +
      'belongs to, so copy the file and add it at ' + rel + ' yourself.';
    return;
  }
  gh.hidden = false;
  var base = 'https://github.com/' + D.repo;
  if (ED.exists) {
    /* The file is already in the repository.  GitHub's edit view will not
     * accept prefilled content, so the honest instruction is copy and paste. */
    gh.href = base + '/edit/' + D.branch + '/' + rel;
    gh.textContent = 'Open this file on GitHub ↗';
    hint.innerHTML = 'This glyph is already a file in the repository. ' +
      'Copy it above, open it on GitHub, select all, paste, and GitHub will ' +
      'offer to open the pull request for you — no clone, no toolchain.';
  } else {
    gh.href = base + '/new/' + D.branch + '?filename=' +
              encodeURIComponent(rel) + '&value=' + encodeURIComponent(text);
    gh.textContent = 'Open a pull request ↗';
    hint.innerHTML = 'There is no file for this glyph yet, so the link above ' +
      'opens GitHub with the path and the drawing already filled in. Commit ' +
      'it and the pull request is done. A drawing beats a computation: this ' +
      'file will override whatever the build produces today.';
  }
}

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && ED) closeEditor();
});
document.addEventListener('click', function (e) {
  if (e.target.id === 'scrim') closeEditor();
});

fetch('data/glyphs.json')
  .then(function (r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  })
  .then(boot)
  .catch(function (err) {
    var p = el('p', 'empty prose',
      'The glyph data did not load (' + err.message + '). This page is ' +
      'built by `make site`; opening index.html straight off disk will not ' +
      'work, because a browser refuses to fetch JSON from file://.');
    $('#grid').appendChild(p);
  });
