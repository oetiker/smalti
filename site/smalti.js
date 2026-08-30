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
  /* Assigned here and not at the top of the file: D is null until the data
   * file has loaded, so a top-level D.guides would throw before anything was
   * drawn.  Read from the build because the build measured them -- the
   * baseline is row 10 at 7x14 and row 11 at 8x16. */
  BASE = D.guides.baseline;
  CAP = D.guides.cap;
  XH = D.guides.xheight;
  AXIS = D.guides.axis;
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
      /* s.z, not s.px: the class names the MULTIPLE.  Built from the pixel
       * size it asked for .s16/.s32/.s48 on the 8x16 page and smalti.css
       * defines .s1/.s2/.s3, so nothing matched and every specimen line fell
       * back to the body size. */
      var line = el('p', 'spec-line px s' + s.z + ' ' + faceClass(f));
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

/* Remembered across glyphs, because the interesting session is "I am drawing
 * a block", not "I am drawing a character".  Private browsing and a blocked
 * storage setting both throw on access rather than returning null, so every
 * read and write is wrapped: the editor has to work with no storage at all. */
var PREF = { repo: 'smalti.repo', branch: 'smalti.branch', hint: 'smalti.hint' };

function pref(key, fallback) {
  try {
    var v = localStorage.getItem(key);
    return v === null ? fallback : v;
  } catch (e) { return fallback; }
}

function setPref(key, value) {
  try { localStorage.setItem(key, value); } catch (e) { /* nothing to do */ }
}

/* Where a pull request goes.  The build knows one repository and one branch;
 * a contributor working through a block wants their edits to land together,
 * so both can be overridden here.  THE SITE CANNOT CREATE A BRANCH -- a
 * GitHub URL only ever opens an editor on a ref that already exists -- so the
 * hint text says so rather than letting a typo look like a broken link. */
function target() {
  return {
    repo: pref(PREF.repo, D.repo) || D.repo,
    branch: pref(PREF.branch, D.branch) || D.branch,
    custom: pref(PREF.repo, D.repo) !== D.repo ||
            pref(PREF.branch, D.branch) !== D.branch
  };
}

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
    exists: k >= 0 && D.layers[face][k] === 'h',
    ghost: pref(PREF.hint, '1') === '1'
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
  /* refresh() has already drawn the guides; this second pass is only for the
   * ghost, once the face for THIS character has actually arrived. */
  var drawn = ED.i;
  ensureHintFont(ghostChar(), function () {
    if (ED && ED.i === drawn) drawOverlay();
  });
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

/* The editor's guide rows, from the build rather than from here.  These were
 * `10, 3, 5, 7` -- 7x14 rows.  The cap line, the x-height line and the maths
 * axis are the same row at 7x14 and 8x16, but THE BASELINE IS NOT: row 10 at
 * 7x14 and row 11 at 8x16, because that is the only type line that moves
 * between the two.  So the 8x16 editor drew its baseline one row high, through
 * the feet of every letter. */
var BASE, CAP, XH, AXIS;

/* ---------------------------------------------------------- the overlay --
 *
 * The four guide lines and the ghost of the character are drawn on ONE canvas
 * sitting over the grid, rather than as pseudo-elements on the cells.  The
 * pseudo-element version had the baseline a pixel below the cell it belonged
 * to, where the next row's own background painted over it -- so the single
 * most important line in the editor was invisible, and no amount of nudging
 * the offset fixes a z-order problem.  A canvas has no siblings to lose to.
 *
 * Every position is measured off the real cell rectangles instead of being
 * recomputed from the CSS.  The cell size changes at a media query, and a
 * second copy of that arithmetic here would be a copy that can disagree. */

function gridGeom(g) {
  var cells = g.querySelectorAll('.pix');
  var w = D.cell.w;
  if (cells.length < w + 2) return null;
  var gr = g.getBoundingClientRect();
  var a = cells[0].getBoundingClientRect();
  var right = cells[1].getBoundingClientRect();
  var below = cells[w].getBoundingClientRect();
  return {
    W: gr.width, H: gr.height,
    x0: a.left - gr.left, y0: a.top - gr.top,
    cw: a.width, ch: a.height,
    px: right.left - a.left, py: below.top - a.top
  };
}

/* Cap height as a fraction of the font size, measured once from the ghost
 * font itself.  Scaling the ghost so ITS capitals land on Smalti's cap line
 * is what makes it traceable; scaling by em box instead leaves every hint a
 * little too tall and the drawing subtly wrong. */
var CAP_RATIO = null;

function capRatio(ctx) {
  if (CAP_RATIO !== null) return CAP_RATIO;
  ctx.save();
  ctx.font = '200px SmaltiHint';
  var m = ctx.measureText('H');
  ctx.restore();
  var a = m && m.actualBoundingBoxAscent;
  /* Safari shipped actualBoundingBoxAscent late; 0.714 is Noto Sans Mono's
   * own cap height, so the fallback is the right answer for the font that
   * owns most of the letters rather than a guess. */
  CAP_RATIO = (a && isFinite(a) && a > 0) ? a / 200 : 0.714;
  return CAP_RATIO;
}

/* A webfont that has not arrived yet measures as the fallback font, and a cap
 * ratio cached from THAT is wrong for the rest of the session.  So wait for
 * the face, throw the cached ratio away, and only then draw. */
function ensureHintFont(ch, done) {
  if (!document.fonts || !document.fonts.load) { done(); return; }
  var probe = 'H' + (ch || '');
  document.fonts.load('200px SmaltiHint', probe).then(function () {
    CAP_RATIO = null;
    done();
  }, done);
}

function ghostChar() {
  var i = ED.i;
  if (D.hint.charAt(i) !== '1') return null;
  if (D.textok.charAt(i) !== '1') return null;
  return String.fromCodePoint(D.cps[i]);
}

function drawOverlay() {
  var host = $('#editor');
  if (!host || !ED) return;
  var g = $('.paint', host);
  var c = $('.ed-overlay', host);
  if (!g || !c) return;
  var m = gridGeom(g);
  if (!m || !m.W) return;

  var dpr = window.devicePixelRatio || 1;
  c.width = Math.round(m.W * dpr);
  c.height = Math.round(m.H * dpr);
  c.style.width = m.W + 'px';
  c.style.height = m.H + 'px';
  var ctx = c.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, m.W, m.H);

  var gapY = m.py - m.ch;
  /* The boundary BELOW a row, which is where the baseline lives: the drawing
   * sits on it, so it is a line between rows and not a line through one. */
  var under = function (row) { return m.y0 + row * m.py + m.ch + gapY / 2; };
  var over = function (row) { return m.y0 + row * m.py - gapY / 2; };
  var baseY = under(BASE);

  if (ED.ghost) {
    var ch = ghostChar();
    if (ch) {
      var rows = BASE + 1 - CAP;            // cap height, in whole cells
      var size = rows * m.py / capRatio(ctx);
      ctx.save();
      ctx.globalAlpha = 0.3;
      ctx.fillStyle = '#8fb3e8';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'alphabetic';
      ctx.font = size + 'px SmaltiHint';
      var mid = m.x0 + ((D.cell.w - 1) * m.px + m.cw) / 2;
      ctx.fillText(ch, mid, baseY);
      ctx.restore();
    }
  }

  /* Four guides, four different lines.  Two of them used to be the same
   * colour at the same opacity, which is no guide at all: you could see that
   * something was marked and not which thing. */
  var lines = [
    [baseY, '#d9a72c', [], 2],              // baseline: solid, and thickest
    [over(CAP), '#5b8bd6', [5, 3], 1],      // cap height: dashed
    [over(XH), '#5b8bd6', [1, 3], 1],       // x-height: dotted
    [m.y0 + AXIS * m.py + m.ch / 2, '#3fa88c', [6, 2, 1, 2], 1]  // maths axis
  ];
  lines.forEach(function (l) {
    ctx.save();
    ctx.strokeStyle = l[1];
    ctx.setLineDash(l[2]);
    ctx.lineWidth = l[3];
    ctx.globalAlpha = 0.9;
    ctx.beginPath();
    var y = Math.round(l[0]) + (l[3] % 2 ? 0.5 : 0);
    ctx.moveTo(0, y);
    ctx.lineTo(m.W, y);
    ctx.stroke();
    ctx.restore();
  });
}

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

  /* Out of flow, so the grid does not see it; aria-hidden and pointer-events
   * none, so neither a screen reader nor a click ever meets it.  Everything it
   * draws is repeated in words in the legend beside it. */
  var c = el('canvas', 'ed-overlay');
  c.setAttribute('aria-hidden', 'true');
  g.appendChild(c);

  /* The cell size changes at a media query and the drawer can be resized, so
   * the overlay follows the grid's real box rather than being drawn once. */
  if (window.ResizeObserver) {
    new ResizeObserver(function () { drawOverlay(); }).observe(g);
  }
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

  /* One row per line, each swatch drawn the way its line is drawn.  Two of
   * these used to share a row and a colour, so the legend could not tell you
   * which blue line was which -- and neither could the grid. */
  var geom = el('ul', 'ed-geom');
  [['solid', 'baseline, under row ' + BASE],
   ['dash', 'cap height, above row ' + CAP],
   ['dot', 'x-height, above row ' + XH],
   ['dashdot', 'maths axis, through row ' + AXIS]].forEach(function (p) {
    var li = el('li');
    var i = el('i', p[0]);
    li.appendChild(i);
    li.appendChild(document.createTextNode(p[1]));
    geom.appendChild(li);
  });
  side.appendChild(geom);

  var ghostRow = el('p', 'ed-toggle');
  var cb = el('input');
  cb.type = 'checkbox';
  cb.id = 'ed-ghost';
  cb.checked = ED.ghost;
  var can = D.hint.charAt(ED.i) === '1' && D.textok.charAt(ED.i) === '1';
  cb.disabled = !can;
  cb.addEventListener('change', function () {
    ED.ghost = cb.checked;
    setPref(PREF.hint, cb.checked ? '1' : '0');
    drawOverlay();
  });
  var lab = el('label', null, can
    ? ' show the character behind the grid'
    : ' no reference glyph exists for this codepoint');
  lab.htmlFor = 'ed-ghost';
  ghostRow.appendChild(cb);
  ghostRow.appendChild(lab);
  side.appendChild(ghostRow);

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

  var alt = el('a', 'ed-alt', '');
  alt.id = 'ed-gh-alt';
  alt.target = '_blank';
  alt.rel = 'noopener';
  alt.hidden = true;
  acts.appendChild(alt);
  side.appendChild(acts);

  var hint = el('p', 'ed-help');
  hint.id = 'ed-hint';
  side.appendChild(hint);

  side.appendChild(targetPanel());
  return side;
}

/* Where the edits go.  Drawing one glyph is a single pull request and the
 * defaults are right; drawing a block is twenty, and they belong together on
 * one branch. */
function targetPanel() {
  var t = target();
  var box = el('details', 'ed-target');
  box.open = t.custom;
  var sum = el('summary', null, 'where edits go');
  box.appendChild(sum);

  var mk = function (id, label, value, placeholder) {
    var p = el('p');
    var l = el('label', null, label);
    l.htmlFor = id;
    var inp = el('input');
    inp.id = id;
    inp.type = 'text';
    inp.value = value || '';
    inp.placeholder = placeholder;
    inp.spellcheck = false;
    inp.autocapitalize = 'none';
    inp.addEventListener('input', function () {
      setPref(id === 'ed-repo' ? PREF.repo : PREF.branch, inp.value.trim());
      refresh();
    });
    p.appendChild(l);
    p.appendChild(inp);
    return p;
  };
  box.appendChild(mk('ed-repo', 'repository', t.repo, 'owner/name'));
  box.appendChild(mk('ed-branch', 'branch', t.branch, D.branch || 'main'));

  var note = el('p', 'ed-help',
    'The branch has to exist already — a GitHub link can open an editor on a '
    + 'branch but cannot create one. Make your first edit the usual way, then '
    + 'paste the branch GitHub made for it here, and everything after it '
    + 'lands on the same branch.');
  box.appendChild(note);

  var reset = el('button', null, 'back to the defaults');
  reset.type = 'button';
  reset.id = 'ed-target-reset';
  reset.addEventListener('click', function () {
    setPref(PREF.repo, D.repo || '');
    setPref(PREF.branch, D.branch || '');
    $('#ed-repo').value = D.repo || '';
    $('#ed-branch').value = D.branch || '';
    refresh();
  });
  box.appendChild(reset);
  return box;
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

  var gh = $('#ed-gh'), alt = $('#ed-gh-alt'), hint = $('#ed-hint');
  var t = target();
  if (!t.repo) {
    gh.hidden = true;
    alt.hidden = true;
    hint.textContent = 'This build does not know which GitHub repository it ' +
      'belongs to, so copy the file and add it at ' + rel + ' yourself.';
    drawOverlay();
    return;
  }
  gh.hidden = false;
  var base = 'https://github.com/' + t.repo;
  var editUrl = base + '/edit/' + t.branch + '/' + rel;
  var newUrl = base + '/new/' + t.branch + '?filename=' +
               encodeURIComponent(rel) + '&value=' + encodeURIComponent(text);
  if (ED.exists) {
    /* The file is already in the repository.  GitHub's edit view will not
     * accept prefilled content, so the honest instruction is copy and paste. */
    gh.href = editUrl;
    gh.textContent = 'Open this file on GitHub ↗';
    hint.innerHTML = 'This glyph is already a file in the repository. ' +
      'Copy it above, open it on GitHub, select all, paste, and GitHub will ' +
      'offer to open the pull request for you — no clone, no toolchain.';
  } else {
    gh.href = newUrl;
    gh.textContent = 'Open a pull request ↗';
    hint.innerHTML = 'There is no file for this glyph yet, so the link above ' +
      'opens GitHub with the path and the drawing already filled in. Commit ' +
      'it and the pull request is done. A drawing beats a computation: this ' +
      'file will override whatever the build produces today.';
  }
  /* On a branch of your own, the build's answer to "does this file exist?"
   * is only true of the default branch: you may have added this very glyph
   * there an hour ago.  Rather than guess, offer the other door as well. */
  alt.hidden = !t.custom;
  if (t.custom) {
    alt.href = ED.exists ? newUrl : editUrl;
    alt.textContent = ED.exists
      ? 'not on ' + t.branch + ' yet? create it ↗'
      : 'already added it to ' + t.branch + '? edit it ↗';
  }
  drawOverlay();
}

/* Registered once, not once per editor: the drawer is rebuilt every time it
 * opens, and a listener added there would accumulate one per glyph looked at.
 * The ResizeObserver in paintGrid covers the cell-size media query; this is
 * the fallback for a browser without one, and for a window resize that does
 * not change the grid's own box (a device-pixel-ratio change on a move
 * between monitors, which the canvas backing store cares about). */
window.addEventListener('resize', function () { drawOverlay(); });

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
