# -*- coding: utf-8 -*-
"""An Eternal Page — desktop-buddy circle, distinct from Visit chatboxes.

Stickers stand on the parchment. The stage iframe is pointer-events:none
(Streamlit sandbox blocks iframe onclick / parent.location). Hits are tested
on the parent page — click to stand near, double-click for one, drag to
rearrange, modifiers and keys for gestures, right-click for a fuller menu.
Whisper into the dock below the stage — not a Visit transcript. No weather,
no ecosystem. Gesture reactions are VFX + pose + mood, never authored speech.
"""
from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Iterable, Optional

STAGE_H = 560
_CLICK_Q = "ep_click"
_SOLO_Q = "ep_solo"
_PET_Q = "ep_pet"
_DRAG_Q = "ep_drag"
_ACT_Q = "ep_act"
_ID_Q = "ep_id"

_CSS_PAGE = """
<style>
html.amp-mode-eternal .st-key-amp_look_chrome { display: none !important; }
html.amp-mode-eternal iframe[data-amp-land="1"],
html.amp-mode-eternal iframe[data-amp-land-life="1"],
html.amp-mode-eternal [data-amp-land-wrap="1"],
html.amp-mode-eternal #amp-land-photo-host,
html.amp-mode-eternal #amp-land-notice-host {
  display: none !important;
}
html.amp-mode-eternal section[data-testid="stMain"],
html.amp-mode-eternal [data-testid="stMainBlockContainer"],
html.amp-mode-eternal .block-container {
  pointer-events: auto !important;
}
iframe[data-amp-eternal="1"],
.st-key-amp_eternal_stage iframe {
  display: block;
  width: 100%;
  max-width: 100%;
  height: __H__px !important;
  border: 0 !important;
  background: transparent !important;
  position: relative !important;
  z-index: 2 !important;
  /* Parent hit-tests companions. Sandbox blocks iframe→parent navigation. */
  pointer-events: none !important;
}
.st-key-amp_eternal_dock,
.st-key-amp_eternal_bar,
.st-key-amp_eternal_names {
  position: relative !important;
  z-index: 6 !important;
  pointer-events: auto !important;
}
.st-key-amp_eternal_bus,
.st-key-amp_eternal_hits {
  position: absolute !important;
  left: -9999px !important;
  width: 1px !important;
  height: 1px !important;
  overflow: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}
#amp-eternal-menu {
  position: fixed;
  z-index: 240;
  min-width: 188px;
  max-height: 70vh;
  overflow-y: auto;
  padding: 6px;
  border-radius: 10px;
  background: rgba(26, 20, 12, .94);
  color: #f7edd2;
  box-shadow: 0 8px 22px rgba(12, 8, 4, .45);
  font: 13px/1.35 "Segoe UI", "Palatino Linotype", Georgia, serif;
  display: none;
}
#amp-eternal-menu button {
  display: block;
  width: 100%;
  margin: 2px 0;
  padding: 6px 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #f7edd2;
  text-align: left;
  cursor: pointer;
}
#amp-eternal-menu button:hover {
  background: rgba(240, 215, 140, .18);
}
</style>
"""

_WATCHER = """
<script>
(function(){
  var doc = window.parent.document;
  var win = window.parent;
  function tabName(el){
    return ((el && el.innerText) || '').replace(/\\s+/g, ' ').trim();
  }
  function sync(){
    var eternal = false;
    try {
      var p = window.parent.location.pathname || '';
      if (/An_Eternal_Page/i.test(p)) eternal = true;
    } catch (e) {}
    if (!eternal) {
      var t = doc.querySelector('[role="tab"][aria-selected="true"]');
      eternal = tabName(t) === 'An Eternal Page';
    }
    doc.documentElement.classList.toggle('amp-mode-eternal', eternal);
    if (eternal) {
      doc.documentElement.classList.add('amp-land-off');
      doc.documentElement.classList.remove('amp-mode-visit', 'amp-mode-walk');
    }
  }
  function sendCmd(cmd){
    if (!cmd) return;
    try {
      var parts = String(cmd).split(':');
      var kind = parts[0];
      var id = parts[1] || '';
      var key = null;
      if (kind === 'click') key = 'amp_eternal_hit_' + id;
      else if (kind === 'solo') key = 'amp_eternal_solo_' + id;
      else if (kind === 'pet') key = 'amp_eternal_pet_' + id;
      if (key) {
        var hitBtn = doc.querySelector('.st-key-' + key + ' button');
        if (hitBtn) { hitBtn.click(); return; }
      }
    } catch (e0) {}
    try {
      var wrap = doc.querySelector('.st-key-amp_eternal_cmd');
      var input = wrap && wrap.querySelector('input, textarea');
      var btn = doc.querySelector('.st-key-amp_eternal_go button');
      if (input && btn) {
        var setter = Object.getOwnPropertyDescriptor(win.HTMLInputElement.prototype, 'value').set;
        setter.call(input, cmd);
        input.dispatchEvent(new win.Event('input', { bubbles: true }));
        input.dispatchEvent(new win.Event('change', { bubbles: true }));
        btn.click();
        return;
      }
    } catch (e) {}
    try {
      var a = doc.createElement('a');
      var u = new URL(win.location.href);
      var parts = String(cmd).split(':');
      var kind = parts[0];
      var id = parts[1] || '';
      if (kind === 'click') u.searchParams.set('ep_click', id);
      else if (kind === 'solo') u.searchParams.set('ep_solo', id);
      else if (kind === 'pet') u.searchParams.set('ep_pet', id);
      else if (kind === 'drag') u.searchParams.set('ep_drag', id + ',' + parts[2] + ',' + parts[3]);
      else {
        u.searchParams.set('ep_act', kind);
        u.searchParams.set('ep_id', id);
      }
      a.href = u.href;
      a.style.display = 'none';
      doc.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e2) {}
  }
  function hideMenu(){
    var m = doc.getElementById('amp-eternal-menu');
    if (m) m.style.display = 'none';
  }
  function showMenu(x, y, cid, label){
    var m = doc.getElementById('amp-eternal-menu');
    if (!m) {
      m = doc.createElement('div');
      m.id = 'amp-eternal-menu';
      doc.body.appendChild(m);
    }
    m.innerHTML = '';
    var title = doc.createElement('div');
    title.textContent = label || cid;
    title.style.cssText = 'padding:4px 10px 6px;opacity:.85;';
    m.appendChild(title);
    function addBtn(text, cmd){
      var b = doc.createElement('button');
      b.type = 'button';
      b.textContent = text;
      b.addEventListener('click', function(ev){
        ev.preventDefault();
        ev.stopPropagation();
        hideMenu();
        sendCmd(cmd);
      });
      m.appendChild(b);
    }
    addBtn('Stand near', 'click:' + cid);
    addBtn('Speak only with them', 'solo:' + cid);
    addBtn('Gentle touch', 'pet:' + cid);
    addBtn('Pat the head', 'pat:' + cid);
    addBtn('Poke', 'poke:' + cid);
    addBtn('Tease', 'tease:' + cid);
    addBtn('Hold hands', 'hands:' + cid);
    addBtn('Hug', 'hug:' + cid);
    addBtn('Wave', 'wave:' + cid);
    addBtn('Comfort', 'comfort:' + cid);
    addBtn('Forehead tap', 'forehead:' + cid);
    addBtn('Cheek poke', 'cheek:' + cid);
    addBtn('Gift-touch', 'gift:' + cid);
    addBtn('Bow', 'bow:' + cid);
    addBtn('Ask how that felt', 'ask:' + cid);
    m.style.left = Math.max(8, x) + 'px';
    m.style.top = Math.max(8, y) + 'px';
    m.style.display = 'block';
  }
  function typingFocus(){
    var el = doc.activeElement;
    if (!el) return false;
    var tag = (el.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
    if (el.isContentEditable) return true;
    try {
      if (el.closest('[data-testid="stTextInput"], [data-testid="stTextArea"], [contenteditable="true"]')) return true;
    } catch (e) {}
    return false;
  }
  function clickGesture(ev){
    var s = !!(ev.shiftKey);
    var c = !!(ev.ctrlKey || ev.metaKey);
    var a = !!(ev.altKey);
    if (s && c) return 'gift';
    if (s && a) return 'cheek';
    if (c && a) return 'comfort';
    if (s) return 'pat';
    if (c) return 'poke';
    if (a) return 'tease';
    return null;
  }
  function dblGesture(ev){
    if (ev.shiftKey) return 'forehead';
    if (ev.ctrlKey || ev.metaKey) return 'hug';
    if (ev.altKey) return 'bow';
    return null;
  }
  function ctxGesture(ev){
    if (ev.shiftKey) return 'hands';
    if (ev.ctrlKey || ev.metaKey) return 'comfort';
    if (ev.altKey) return 'wave';
    return null;
  }
  function activeStage(){
    if (!doc.documentElement.classList.contains('amp-mode-eternal')) return null;
    var frames = doc.querySelectorAll('iframe[data-amp-eternal="1"], .st-key-amp_eternal_stage iframe');
    for (var i = 0; i < frames.length; i++) {
      var fr = frames[i];
      if (!fr || !fr.isConnected) continue;
      var panel = fr.closest('[data-testid="stTabPanel"]');
      if (panel && (panel.hidden || panel.getAttribute('aria-hidden') === 'true')) continue;
      var rect = fr.getBoundingClientRect();
      if (rect.width < 40 || rect.height < 40) continue;
      return fr;
    }
    return null;
  }
  function chromeHit(el){
    if (!el || !el.closest) return false;
    return !!el.closest(
      '.st-key-amp_look_chrome, [role="tablist"], [data-testid="stHeader"], ' +
      'section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], ' +
      '.st-key-amp_eternal_bar, .st-key-amp_eternal_dock, .st-key-amp_eternal_names, ' +
      '#amp-eternal-menu, [data-testid="stBottomBlockContainer"]'
    );
  }
  function iframePoint(fr, ev){
    var idoc = fr.contentDocument;
    if (!idoc) return null;
    var rect = fr.getBoundingClientRect();
    var w = rect.width || 1;
    var h = rect.height || 1;
    var iw = (idoc.documentElement && idoc.documentElement.clientWidth) || w;
    var ih = (idoc.documentElement && idoc.documentElement.clientHeight) || h;
    var x = (ev.clientX - rect.left) * (iw / w);
    var y = (ev.clientY - rect.top) * (ih / h);
    if (x < 0 || y < 0 || x > iw || y > ih) return null;
    return { x: x, y: y, idoc: idoc, rect: rect };
  }
  function hitBuddy(ev){
    var fr = activeStage();
    if (!fr) return null;
    var top = doc.elementFromPoint(ev.clientX, ev.clientY);
    if (chromeHit(top)) return null;
    var pt = iframePoint(fr, ev);
    if (!pt) return null;
    try {
      var inner = pt.idoc.elementFromPoint(pt.x, pt.y);
      if (!inner || !inner.closest) return null;
      var buddy = inner.closest('.buddy');
      if (!buddy) return null;
      return { buddy: buddy, idoc: pt.idoc, fr: fr, pt: pt };
    } catch (e) {
      return null;
    }
  }
  function placePercents(hit, ev){
    var stage = hit.idoc.querySelector('[data-amp-eternal-stage="1"]') || hit.idoc.body;
    var sw = stage.clientWidth || 1;
    var sh = stage.clientHeight || 1;
    var left = (hit.pt.x / sw) * 100;
    var bottom = (1 - (hit.pt.y / sh)) * 100;
    if (left < 4) left = 4;
    if (left > 96) left = 96;
    if (bottom < 8) bottom = 8;
    if (bottom > 88) bottom = 88;
    return { left: left, bottom: bottom };
  }
  sync();
  doc.addEventListener('click', function(){ setTimeout(sync, 40); }, true);
  try {
    new MutationObserver(sync).observe(doc.body, {
      attributes: true, subtree: true, attributeFilter: ['aria-selected']
    });
  } catch (e) {}

  if (doc.__ampEternalBound) return;
  doc.__ampEternalBound = true;

  var drag = null;
  var clickTimer = null;
  var lastId = '';
  var skipClick = false;
  var hoverId = '';
  var keyMap = {p:'pat', h:'hug', f:'hands', w:'wave', c:'comfort', g:'gift', b:'bow', t:'forehead', k:'cheek'};

  doc.addEventListener('pointerdown', function(ev){
    if (ev.button !== 0) return;
    hideMenu();
    var hit = hitBuddy(ev);
    if (!hit) return;
    var id = hit.buddy.getAttribute('data-heir') || '';
    if (!id) return;
    drag = {
      id: id,
      buddy: hit.buddy,
      x: ev.clientX,
      y: ev.clientY,
      moved: false
    };
    hit.buddy.classList.add('grabbing');
  }, true);

  doc.addEventListener('pointermove', function(ev){
    var live = hitBuddy(ev);
    if (live) {
      hoverId = live.buddy.getAttribute('data-heir') || '';
    } else {
      var fr = activeStage();
      if (!fr) hoverId = '';
      else {
        var rect = fr.getBoundingClientRect();
        if (ev.clientX < rect.left || ev.clientY < rect.top || ev.clientX > rect.right || ev.clientY > rect.bottom) hoverId = '';
      }
    }
    if (!drag) return;
    var dx = ev.clientX - drag.x;
    var dy = ev.clientY - drag.y;
    if (!drag.moved && (dx * dx + dy * dy) < 64) return;
    drag.moved = true;
    var fr = activeStage();
    if (!fr) return;
    var pt = iframePoint(fr, ev);
    if (!pt) return;
    var fake = { buddy: drag.buddy, idoc: pt.idoc, fr: fr, pt: pt };
    var place = placePercents(fake, ev);
    drag.buddy.style.left = place.left + '%';
    drag.buddy.style.bottom = place.bottom + '%';
    drag.left = place.left;
    drag.bottom = place.bottom;
  }, true);

  doc.addEventListener('pointerup', function(ev){
    if (!drag) return;
    var info = drag;
    drag = null;
    try { info.buddy.classList.remove('grabbing'); } catch (e) {}
    if (info.moved) {
      skipClick = true;
      clearTimeout(clickTimer);
      sendCmd('drag:' + info.id + ':' + (info.left || 50).toFixed(1) + ':' + (info.bottom || 50).toFixed(1));
      return;
    }
  }, true);

  doc.addEventListener('click', function(ev){
    if (ev.button !== 0) return;
    if (skipClick) { skipClick = false; return; }
    var hit = hitBuddy(ev);
    if (!hit) return;
    var id = hit.buddy.getAttribute('data-heir') || '';
    if (!id) return;
    ev.preventDefault();
    ev.stopPropagation();
    clearTimeout(clickTimer);
    lastId = id;
    var gest = clickGesture(ev);
    if (gest) {
      sendCmd(gest + ':' + id);
      return;
    }
    clickTimer = setTimeout(function(){ sendCmd('click:' + id); }, 220);
  }, true);

  doc.addEventListener('dblclick', function(ev){
    var hit = hitBuddy(ev);
    if (!hit) return;
    var id = hit.buddy.getAttribute('data-heir') || lastId;
    if (!id) return;
    ev.preventDefault();
    ev.stopPropagation();
    clearTimeout(clickTimer);
    var gest = dblGesture(ev);
    sendCmd((gest || 'solo') + ':' + id);
  }, true);

  doc.addEventListener('contextmenu', function(ev){
    var hit = hitBuddy(ev);
    if (!hit) return;
    ev.preventDefault();
    ev.stopPropagation();
    var id = hit.buddy.getAttribute('data-heir') || '';
    var gest = ctxGesture(ev);
    if (gest) {
      sendCmd(gest + ':' + id);
      return;
    }
    var label = '';
    try { label = (hit.buddy.querySelector('.name') || {}).textContent || id; } catch (e) { label = id; }
    showMenu(ev.clientX, ev.clientY, id, label);
  }, true);

  doc.addEventListener('click', function(ev){
    var m = doc.getElementById('amp-eternal-menu');
    if (!m || m.style.display === 'none') return;
    if (ev.target && m.contains(ev.target)) return;
    hideMenu();
  }, false);

  doc.addEventListener('keydown', function(ev){
    if (typingFocus()) return;
    if (!doc.documentElement.classList.contains('amp-mode-eternal')) return;
    if (!hoverId) return;
    var g = keyMap[(ev.key || '').toLowerCase()];
    if (!g) return;
    ev.preventDefault();
    ev.stopPropagation();
    sendCmd(g + ':' + hoverId);
  }, true);
})();
</script>
"""


def _data_uri(path: Path) -> str:
    raw = path.read_bytes()
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def _bytes_uri(raw: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def _art_parts(entry) -> tuple[str, str, str]:
    """Return (body_uri, face_uri, kind) from a string or dict art entry."""
    if isinstance(entry, dict):
        body = str(entry.get("body") or entry.get("src") or "")
        face = str(entry.get("face") or "")
        kind = str(entry.get("kind") or "ppg")
        return body, face, kind if kind in {"q", "ppg"} else "ppg"
    return str(entry or ""), "", "ppg"


_VFX_MARK_NAMES = (
    "flush", "vein", "steam", "sweat", "tear", "sparkle", "heart", "query",
    "bang", "dizzy", "zzz", "shock", "flower", "ice", "veil", "note", "shy", "glow",
)

_STAGE_VFX_CSS = """
.sprite { position: relative; display: block; }
.vfx {
  position: absolute; left: 0; right: 0; top: 0; bottom: 0;
  z-index: 4; pointer-events: none; overflow: visible;
}
.mk { position: absolute; display: none; pointer-events: none; line-height: 1; }
.buddy[data-amp-emotion="warm"] .mk-flush,
.buddy[data-amp-vfx~="flush"] .mk-flush { display: block; }
.buddy[data-amp-emotion="anger"] .mk-vein,
.buddy[data-amp-vfx~="vein"] .mk-vein { display: block; }
.buddy[data-amp-emotion="anger"] .mk-steam,
.buddy[data-amp-vfx~="steam"] .mk-steam { display: block; }
.buddy[data-amp-emotion="fear"] .mk-sweat,
.buddy[data-amp-vfx~="sweat"] .mk-sweat { display: block; }
.buddy[data-amp-emotion="sad"] .mk-tear,
.buddy[data-amp-vfx~="tear"] .mk-tear { display: block; }
.buddy[data-amp-emotion="joy"] .mk-sparkle,
.buddy[data-amp-emotion="tease"] .mk-sparkle,
.buddy[data-amp-vfx~="sparkle"] .mk-sparkle { display: block; }
.buddy[data-amp-emotion="joy"] .mk-heart,
.buddy[data-amp-vfx~="heart"] .mk-heart { display: block; }
.buddy[data-amp-vfx~="query"] .mk-query { display: block; }
.buddy[data-amp-emotion="surprise"] .mk-bang,
.buddy[data-amp-vfx~="bang"] .mk-bang { display: block; }
.buddy[data-amp-vfx~="dizzy"] .mk-dizzy { display: block; }
.buddy[data-amp-emotion="weary"] .mk-zzz,
.buddy[data-amp-vfx~="zzz"] .mk-zzz { display: block; }
.buddy[data-amp-emotion="surprise"] .mk-shock,
.buddy[data-amp-vfx~="shock"] .mk-shock { display: block; }
.buddy[data-amp-vfx~="flower"] .mk-flower { display: block; }
.buddy[data-amp-vfx~="ice"] .mk-ice { display: block; }
.buddy[data-amp-emotion="sad"] .mk-veil,
.buddy[data-amp-vfx~="veil"] .mk-veil { display: block; }
.buddy[data-amp-vfx~="note"] .mk-note { display: block; }
.buddy[data-amp-vfx~="shy"] .mk-shy { display: block; }
.buddy[data-amp-emotion="calm"] .mk-glow,
.buddy[data-amp-vfx~="glow"] .mk-glow { display: block; }

.mk-flush { inset: 40% 8% 18% 8%; }
.mk-flush::before, .mk-flush::after {
  content: ""; position: absolute; width: 36%; height: 58%; border-radius: 50%;
  background: radial-gradient(circle, rgba(255,108,138,.78) 0%, rgba(255,108,138,0) 72%);
  top: 8%;
}
.mk-flush::before { left: 0; }
.mk-flush::after { right: 0; }

.mk-vein { top: -2%; right: 2%; font-size: 15px; }
.mk-vein::after { content: "💢"; filter: drop-shadow(0 0 2px #4a1010); }

.mk-steam { top: -10%; left: 28%; width: 44%; height: 28%; }
.mk-steam::before, .mk-steam::after {
  content: ""; position: absolute; width: 28%; height: 100%;
  border-radius: 40px; opacity: .75;
  background: linear-gradient(180deg, rgba(255,255,255,.85), transparent);
  animation: amp-steam 1.4s ease-in-out infinite;
}
.mk-steam::before { left: 12%; }
.mk-steam::after { right: 8%; animation-delay: .35s; }

.mk-sweat { top: 2%; left: 2%; font-size: 13px; }
.mk-sweat::after { content: "💧"; }

.mk-tear { top: 46%; left: 16%; font-size: 12px; }
.mk-tear::after { content: "💧"; animation: amp-fall 1.5s ease-in infinite; }

.mk-sparkle { top: 4%; left: 6%; font-size: 13px; color: #ffe9a0; }
.mk-sparkle::after { content: "✦"; animation: amp-twinkle .9s ease-in-out infinite; }

.mk-heart { top: -6%; right: 10%; font-size: 14px; color: #ff5a7a; }
.mk-heart::after { content: "♥"; animation: amp-float 1.2s ease-in-out infinite; }

.mk-query { top: -8%; left: 40%; font-size: 16px; color: #fff4d0;
  font-weight: 800; text-shadow: 0 1px 2px #1a140c; }
.mk-query::after { content: "?"; }

.mk-bang { top: -8%; left: 42%; font-size: 16px; color: #fff4d0;
  font-weight: 800; text-shadow: 0 1px 2px #1a140c; }
.mk-bang::after { content: "!"; }

.mk-dizzy { top: -6%; left: 34%; font-size: 14px; }
.mk-dizzy::after { content: "🌀"; animation: amp-spin 1.2s linear infinite; }

.mk-zzz { top: -4%; right: 6%; font-size: 11px; color: #dce6ff;
  letter-spacing: .04em; text-shadow: 0 1px 2px #1a140c; }
.mk-zzz::after { content: "zzz"; animation: amp-float 1.6s ease-in-out infinite; }

.mk-shock { inset: -6% -4% 40% -4%; }
.mk-shock::before, .mk-shock::after {
  content: ""; position: absolute; inset: 8% 10%;
  background:
    linear-gradient(25deg, transparent 46%, #fff8dc 46%, #fff8dc 54%, transparent 54%),
    linear-gradient(-25deg, transparent 46%, #fff8dc 46%, #fff8dc 54%, transparent 54%),
    linear-gradient(90deg, transparent 46%, #fff8dc 46%, #fff8dc 54%, transparent 54%);
  opacity: .85; animation: amp-twinkle .45s steps(2, end) infinite;
}
.mk-shock::after { transform: scaleX(-1); }

.mk-flower { top: 0; left: 8%; font-size: 13px; color: #ffb6c8; }
.mk-flower::after { content: "✿"; }

.mk-ice { top: 2%; right: 14%; font-size: 13px; color: #c8eeff; }
.mk-ice::after { content: "❄"; filter: drop-shadow(0 0 3px #8fd4ff); }

.mk-veil {
  inset: 4% 6% 10% 6%; border-radius: 46%;
  background: radial-gradient(circle, rgba(40,24,72,.0) 30%, rgba(28,16,48,.45) 100%);
  display: none;
}
.buddy[data-amp-emotion="sad"] .mk-veil,
.buddy[data-amp-vfx~="veil"] .mk-veil { display: block; }

.mk-note { top: -4%; left: 18%; font-size: 13px; color: #c9b6ff; }
.mk-note::after { content: "♪"; animation: amp-float 1.4s ease-in-out infinite; }

.mk-shy { left: 18%; right: 18%; bottom: 10%; height: 22%; }
.mk-shy::before, .mk-shy::after {
  content: ""; position: absolute; width: 38%; height: 90%;
  border-radius: 40% 40% 30% 30%;
  background: rgba(255, 228, 210, .92);
  box-shadow: 0 1px 2px rgba(40,20,10,.35);
  bottom: 0;
}
.mk-shy::before { left: 0; transform: rotate(-12deg); }
.mk-shy::after { right: 0; transform: rotate(12deg); }

.mk-glow {
  inset: 8% 10% 12% 10%; border-radius: 50%;
  background: radial-gradient(circle, rgba(180,210,255,.35), transparent 70%);
}
.buddy[data-amp-gesture] .mk { animation: amp-pop .45s ease-out; }
@keyframes amp-pop {
  0% { transform: scale(.45); opacity: 0; }
  45% { transform: scale(1.12); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}
@keyframes amp-twinkle {
  0%, 100% { opacity: .35; transform: scale(.85); }
  50% { opacity: 1; transform: scale(1.1); }
}
@keyframes amp-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}
@keyframes amp-steam {
  0%, 100% { transform: translateY(6px) scaleY(.7); opacity: .15; }
  50% { transform: translateY(-4px) scaleY(1); opacity: .8; }
}
@keyframes amp-fall {
  0% { transform: translateY(0); opacity: .9; }
  100% { transform: translateY(6px); opacity: .2; }
}
@keyframes amp-spin { to { transform: rotate(360deg); } }
.legend {
  position: absolute;
  left: 10px;
  bottom: 8px;
  z-index: 6;
  max-width: 54%;
  color: #f7edd2;
  font-size: 10px;
  line-height: 1.35;
  text-shadow: 0 1px 3px #1a140c;
  pointer-events: none;
  opacity: .88;
}
"""


def _vfx_marks_html() -> str:
    inner = "".join(f'<i class="mk mk-{name}"></i>' for name in _VFX_MARK_NAMES)
    return f'<span class="vfx" aria-hidden="true">{inner}</span>'


def _mark_iframe_js() -> str:
    return """
(function(){
  try {
    var f = window.frameElement;
    if (f) {
      f.setAttribute('data-amp-eternal', '1');
      f.setAttribute('scrolling', 'no');
    }
  } catch (e) {}
  function passWheel(e){
    try { window.parent.scrollBy(0, e.deltaY); } catch (err) {}
  }
  document.addEventListener('wheel', passWheel, {passive: true});
  document.addEventListener('mousewheel', passWheel, {passive: true});
})();
"""


def build_stage_html(
    *,
    selected: Iterable[str],
    bubbles: Optional[list] = None,
    art: Optional[dict] = None,
    parchment_uri: str = "",
    names: Optional[dict] = None,
    emotions: Optional[dict] = None,
    layout: Optional[dict] = None,
    gestures: Optional[dict] = None,
) -> str:
    from src.world import eternal_page as ep
    from src.world.eternal_emotion import vfx_for
    from src.world.eternal_gesture import legend_html, overlay_fresh

    selected_ids = ep.normalize_selected(selected)
    art = art or {}
    names = names or {}
    emotions = emotions or {}
    gestures = gestures or {}
    bubble_by = {}
    for row in bubbles or []:
        cid = str(row.get("id") or "")
        text = str(row.get("text") or "").strip()
        if cid and text:
            bubble_by[cid] = text

    vfx_bits = _vfx_marks_html()
    buddies = []
    for cid in ep.all_ids():
        src = art.get(cid) or ""
        body_src, face_src, kind = _art_parts(src)
        if not body_src:
            continue
        left, bottom = ep.place_of(cid, layout)
        on = " on" if cid in selected_ids else ""
        label = html.escape(names.get(cid) or ep.short_name(cid))
        raw_feel = str(emotions.get(cid) or "calm")
        feeling = html.escape(raw_feel)
        row = gestures.get(cid) if isinstance(gestures.get(cid), dict) else None
        marks = list(vfx_for(emotions.get(cid) or "calm"))
        gest_name = ""
        if row and overlay_fresh(row):
            gest_name = html.escape(str(row.get("gesture") or ""))
            for m in row.get("vfx") or []:
                if m not in marks:
                    marks.append(str(m))
        vfx_attr = html.escape(" ".join(str(m) for m in marks if m))
        spoken = bubble_by.get(cid, "")
        bubble = ""
        if spoken:
            bubble = (
                f'<div class="bubble" data-amp-bubble="1">'
                f"{html.escape(spoken)}</div>"
            )
        gest_attr = f' data-amp-gesture="{gest_name}"' if gest_name else ""
        show_face = (
            kind == "q"
            and bool(face_src)
            and (
                cid in selected_ids
                or raw_feel not in {"calm", ""}
                or bool(gest_name)
                or bool(spoken)
            )
        )
        face_cls = " show-face" if show_face else ""
        face_img = ""
        if face_src and kind == "q":
            face_img = (
                f'<img class="face" alt="" src="{face_src}" draggable="false" />'
            )
        buddies.append(
            f'<button type="button" class="buddy{on}{face_cls}" data-heir="{html.escape(cid)}" '
            f'data-amp-emotion="{feeling}" data-amp-vfx="{vfx_attr}" '
            f'data-amp-body="{html.escape(kind)}"{gest_attr} '
            f'title="{label} — click, drag, right-click, or hover keys" '
            f'style="left:{left}%;bottom:{bottom}%;z-index:{7 if cid in selected_ids else 2}">'
            f"{bubble}"
            f'<span class="sprite">'
            f'<img class="body" alt="{label}" src="{body_src}" draggable="false" />'
            f"{face_img}"
            f"{vfx_bits}"
            f"</span>"
            f'<span class="name">{label}</span>'
            f"</button>"
        )

    bg = ""
    if parchment_uri:
        bg = (
            f"background-image:url('{parchment_uri}');"
            "background-size:cover;background-position:center;"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
html, body {{
  margin: 0; padding: 0; width: 100%; height: 100%;
  overflow: hidden; background: #07101c;
  font-family: "Segoe UI", "Palatino Linotype", Georgia, serif;
}}
.stage {{
  position: relative;
  width: 100%;
  height: 100%;
  {bg}
  background-color: #0c1a38;
}}
.stage::before {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background:
    radial-gradient(ellipse at 50% 28%, rgba(160,190,255,.16), transparent 58%),
    linear-gradient(180deg, rgba(6,12,28,.10), rgba(6,12,28,.34));
}}
.buddy {{
  position: absolute;
  width: 13.2%;
  min-width: 72px;
  transform: translateX(-50%);
  background: none;
  border: 0;
  padding: 0;
  cursor: grab;
  pointer-events: auto;
}}
.buddy[data-amp-body="q"] {{
  width: 15.2%;
}}
.buddy.grabbing {{
  cursor: grabbing;
  z-index: 9 !important;
}}
.buddy .sprite {{
  height: 228px;
  overflow: visible;
}}
.buddy img.body {{
  display: block;
  width: 100%;
  height: 100%;
  max-height: 228px;
  object-fit: contain;
  object-position: bottom center;
  user-select: none;
  -webkit-user-drag: none;
  filter: drop-shadow(0 8px 10px rgba(20,12,6,.45));
}}
.buddy img.face {{
  display: none;
  position: absolute;
  width: 46%;
  right: -8%;
  top: 0;
  height: auto;
  z-index: 3;
  pointer-events: none;
  user-select: none;
  -webkit-user-drag: none;
  filter: drop-shadow(0 4px 8px rgba(20,12,6,.55));
}}
.buddy.show-face img.face {{
  display: block;
}}
.buddy.on img.body {{
  filter: drop-shadow(0 0 10px rgba(240,215,140,.95)) drop-shadow(0 8px 10px rgba(20,12,6,.45));
}}
.buddy .name {{
  display: block;
  margin-top: 2px;
  color: #f7edd2;
  font-size: 12px;
  letter-spacing: .04em;
  text-align: center;
  text-shadow: 0 1px 2px #1a140c, 0 0 6px #1a140c;
}}
.buddy.on::after {{
  content: "";
  position: absolute;
  left: 18%;
  right: 18%;
  bottom: 16px;
  height: 10px;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(ellipse, rgba(240,215,140,.7), transparent 70%);
}}
.bubble {{
  position: absolute;
  left: 50%;
  bottom: 92%;
  transform: translateX(-50%);
  z-index: 8;
  max-width: 220px;
  min-width: 90px;
  padding: 8px 10px;
  border-radius: 14px 14px 14px 4px;
  background: rgba(255,250,240,.94);
  color: #2a2014;
  font-size: 12px;
  line-height: 1.35;
  box-shadow: 0 4px 14px rgba(20,12,6,.28);
  pointer-events: none;
}}
.hint {{
  position: absolute;
  top: 10px;
  left: 14px;
  z-index: 6;
  color: #f7edd2;
  font-size: 13px;
  text-shadow: 0 1px 3px #1a140c;
  pointer-events: none;
}}
{_STAGE_VFX_CSS}
</style>
</head>
<body>
<div class="stage" data-amp-eternal-stage="1">
  <div class="hint">Click to stand near · double-click for one · drag to move · right-click for more · Shift+click to pat</div>
  {''.join(buddies)}
  {legend_html()}
</div>
<script>
{_mark_iframe_js()}
(function(){{
  /* Backup if the iframe still receives clicks. Parent hit-test is the real path
     (ep_click / ep_solo / ep_pet / ep_drag). Sandbox blocks parent.location. */
  function sendCmd(cmd){{
    try {{
      var pdoc = window.parent.document;
      var pwin = window.parent;
      var parts = String(cmd).split(':');
      var kind = parts[0];
      var id = parts[1] || '';
      var key = null;
      if (kind === 'click') key = 'amp_eternal_hit_' + id;
      else if (kind === 'solo') key = 'amp_eternal_solo_' + id;
      else if (kind === 'pet') key = 'amp_eternal_pet_' + id;
      if (key) {{
        var hitBtn = pdoc.querySelector('.st-key-' + key + ' button');
        if (hitBtn) {{ hitBtn.click(); return; }}
      }}
      var wrap = pdoc.querySelector('.st-key-amp_eternal_cmd');
      var input = wrap && wrap.querySelector('input, textarea');
      var btn = pdoc.querySelector('.st-key-amp_eternal_go button');
      if (input && btn) {{
        var setter = Object.getOwnPropertyDescriptor(pwin.HTMLInputElement.prototype, 'value').set;
        setter.call(input, cmd);
        input.dispatchEvent(new pwin.Event('input', {{ bubbles: true }}));
        btn.click();
        return;
      }}
    }} catch (e) {{}}
    try {{
      var a = window.parent.document.createElement('a');
      var u = new URL(window.parent.location.href);
      var parts = String(cmd).split(':');
      if (parts[0] === 'click') u.searchParams.set('ep_click', parts[1]);
      else if (parts[0] === 'solo') u.searchParams.set('ep_solo', parts[1]);
      else if (parts[0] === 'pet') u.searchParams.set('ep_pet', parts[1]);
      else if (parts[0] === 'drag') u.searchParams.set('ep_drag', parts[1] + ',' + parts[2] + ',' + parts[3]);
      else {{
        u.searchParams.set('ep_act', parts[0]);
        u.searchParams.set('ep_id', parts[1]);
      }}
      a.href = u.href;
      a.style.display = 'none';
      window.parent.document.body.appendChild(a);
      a.click();
      a.remove();
    }} catch (e2) {{}}
  }}
  var timers = {{}};
  document.querySelectorAll('.buddy').forEach(function(el){{
    var id = el.getAttribute('data-heir');
    el.addEventListener('click', function(e){{
      e.preventDefault();
      e.stopPropagation();
      clearTimeout(timers[id]);
      timers[id] = setTimeout(function(){{ sendCmd('click:' + id); }}, 220);
    }});
    el.addEventListener('dblclick', function(e){{
      e.preventDefault();
      e.stopPropagation();
      clearTimeout(timers[id]);
      sendCmd('solo:' + id);
    }});
  }});
}})();
</script>
</body>
</html>
"""


def _do_gesture(st, cid: str, gesture: str, world=None) -> bool:
    from src.world import eternal_page as ep
    from src.world.eternal_gesture import GESTURE_IDS, apply_gesture

    if gesture not in GESTURE_IDS:
        return False
    overlay = dict(st.session_state.get(ep.STATE_GESTURES) or {})
    near = ep.normalize_selected(st.session_state.get(ep.STATE_SELECTED))
    result = apply_gesture(cid, gesture, world=world, overlay=overlay, near=near)
    st.session_state[ep.STATE_GESTURES] = result.get("overlay") or overlay
    if result.get("join_near") and cid not in near:
        st.session_state[ep.STATE_SELECTED] = ep.normalize_selected(list(near) + [cid])
    return bool(result.get("ok"))


def _ask_felt(st, cid: str, manager) -> bool:
    from src.world import eternal_page as ep
    from src.world.eternal_gesture import ASK_USER_LINE

    if manager is None:
        return False
    selected = ep.normalize_selected(st.session_state.get(ep.STATE_SELECTED))
    if cid not in selected:
        selected = ep.normalize_selected(list(selected) + [cid])
        st.session_state[ep.STATE_SELECTED] = selected
    names = _names(manager)
    result = ep.eternal_talk(
        manager,
        [cid],
        ASK_USER_LINE,
        everyone=False,
        rotate=int(st.session_state.get(ep.STATE_ROTATE) or 0),
        name_of=lambda c: names.get(c, ep.short_name(c)),
    )
    if result.get("ok"):
        st.session_state[ep.STATE_BUBBLES] = result.get("replies") or []
        st.session_state[ep.STATE_ROTATE] = result.get("next_rotate") or 0
    return True


def _apply_command(st, raw: str, manager=None, world=None) -> bool:
    from src.world import eternal_page as ep
    from src.world.eternal_gesture import GESTURE_IDS

    parsed = ep.parse_command(raw)
    if not parsed:
        return False
    kind = parsed[0]
    cid = parsed[1]
    selected = ep.normalize_selected(st.session_state.get(ep.STATE_SELECTED))
    if kind == "click":
        st.session_state[ep.STATE_SELECTED] = ep.toggle_member(selected, cid)
        return True
    if kind == "solo":
        st.session_state[ep.STATE_SELECTED] = ep.solo_member(cid)
        return True
    if kind == "drag":
        layout = dict(st.session_state.get(ep.STATE_LAYOUT) or {})
        st.session_state[ep.STATE_LAYOUT] = ep.move_companion(layout, cid, parsed[2], parsed[3])
        return True
    if kind == "ask":
        return _ask_felt(st, cid, manager)
    if kind in GESTURE_IDS:
        return _do_gesture(st, cid, kind, world=world)
    return False


def _clear_query(st, *keys: str) -> None:
    for key in keys:
        try:
            del st.query_params[key]
        except Exception:
            pass


def _consume_clicks(st, bus_go: bool = False, manager=None) -> bool:
    from src.world import eternal_page as ep
    from src.world.eternal_gesture import commands_from_query

    changed = False
    params = {}
    try:
        qp = st.query_params
        for key in (_CLICK_Q, _SOLO_Q, _PET_Q, _DRAG_Q, _ACT_Q, _ID_Q):
            params[key] = qp.get(key)
    except Exception:
        params = {}
    for cmd in commands_from_query(params):
        if _apply_command(st, cmd, manager=manager):
            changed = True
    if any(params.get(k) for k in (_CLICK_Q, _SOLO_Q, _PET_Q, _DRAG_Q, _ACT_Q, _ID_Q)):
        _clear_query(st, _CLICK_Q, _SOLO_Q, _PET_Q, _DRAG_Q, _ACT_Q, _ID_Q)
    payload = str(st.session_state.get(ep.STATE_CMD) or "").strip()
    if bus_go and payload:
        st.session_state[ep.STATE_CMD] = ""
        if _apply_command(st, payload, manager=manager):
            changed = True
    return changed


def _names(manager) -> dict:
    from src.world import eternal_page as ep

    out = {}
    for cid in ep.all_ids():
        name = ep.short_name(cid)
        try:
            info = manager.get_character_info(cid)
            raw = str((info or {}).get("name") or "").strip()
            if raw:
                if cid == "dan-heng-permansor-terrae":
                    name = "Dan Heng"
                else:
                    name = raw.split("•")[0].strip() or raw
        except Exception:
            pass
        out[cid] = name
    return out


def render_eternal_page(manager, *, key_prefix: str = "eternal") -> None:
    import streamlit as st
    import streamlit.components.v1 as components

    from src.ui_role import is_visitor
    from src.world import eternal_page as ep

    st.markdown(_CSS_PAGE.replace("__H__", str(STAGE_H)), unsafe_allow_html=True)
    try:
        components.html(_WATCHER, height=0, scrolling=False)
    except Exception:
        pass

    with st.container(key="amp_eternal_bus"):
        st.text_input("ep_cmd", key=ep.STATE_CMD, label_visibility="collapsed")
        bus_go = st.button("go", key="amp_eternal_go")

    if ep.STATE_SELECTED not in st.session_state:
        st.session_state[ep.STATE_SELECTED] = list(ep.all_ids())
    hit_changed = False
    with st.container(key="amp_eternal_hits"):
        for cid in ep.all_ids():
            if st.button("hit", key=f"amp_eternal_hit_{cid}"):
                cur = ep.normalize_selected(st.session_state.get(ep.STATE_SELECTED))
                st.session_state[ep.STATE_SELECTED] = ep.toggle_member(cur, cid)
                hit_changed = True
            if st.button("solo", key=f"amp_eternal_solo_{cid}"):
                st.session_state[ep.STATE_SELECTED] = ep.solo_member(cid)
                hit_changed = True
            if st.button("pet", key=f"amp_eternal_pet_{cid}"):
                _do_gesture(st, cid, "pet")
                hit_changed = True

    if hit_changed or _consume_clicks(st, bus_go=bus_go, manager=manager):
        st.rerun()
    if ep.STATE_LAYOUT not in st.session_state:
        st.session_state[ep.STATE_LAYOUT] = {}
    if ep.STATE_GESTURES not in st.session_state:
        st.session_state[ep.STATE_GESTURES] = {}
    selected = ep.normalize_selected(st.session_state.get(ep.STATE_SELECTED))
    layout = dict(st.session_state.get(ep.STATE_LAYOUT) or {})
    from src.world.eternal_gesture import legend_caption, prune_overlay
    gestures = prune_overlay(st.session_state.get(ep.STATE_GESTURES))
    st.session_state[ep.STATE_GESTURES] = gestures
    bubbles = list(st.session_state.get(ep.STATE_BUBBLES) or [])
    names = _names(manager)
    try:
        from src.world.eternal_emotion import circle_emotions
        emotions = circle_emotions(manager, bubbles=bubbles, gestures=gestures)
    except Exception:
        emotions = {cid: "calm" for cid in ep.all_ids()}

    st.title("An Eternal Page")
    st.caption(
        "Beyond Time — the memory-space of As I've Written, not a city on the map. "
        "This is not Visit an Heir: special-program Q sitters stand on the star-swirl "
        "page, with Pom-Pom Gallery faces when someone is near or feeling. "
        "The same memories are kept."
    )
    st.caption(legend_caption())

    missing = ep.art_missing()
    if missing:
        st.warning(
            "Cute companion art is missing for: "
            + ", ".join(ep.short_name(c) for c in missing)
            + ". Run `python tools/fetch_eternal_page_art.py`."
        )

    with st.container(key="amp_eternal_bar"):
        c1, c2, c3, c4 = st.columns([1.2, 1.2, 2.2, 3])
        with c1:
            if st.button("All thirteen", key=f"{key_prefix}_all"):
                st.session_state[ep.STATE_SELECTED] = list(ep.all_ids())
                st.rerun()
        with c2:
            if st.button("Clear", key=f"{key_prefix}_clear"):
                st.session_state[ep.STATE_SELECTED] = []
                st.rerun()
        with c3:
            everyone = st.checkbox(
                "Everyone near answers",
                key=ep.STATE_EVERYONE,
                help="When off, a handful answer and the rest still hear you.",
            )
        with c4:
            if selected:
                st.caption(
                    "Standing near: "
                    + ", ".join(names.get(c, c) for c in selected)
                )
            else:
                st.caption("No one is standing near yet — click a companion.")

    with st.container(key="amp_eternal_names"):
        st.caption("Tap a name if the picture does not answer:")
        row1 = ep.all_ids()[:7]
        row2 = ep.all_ids()[7:]
        for row in (row1, row2):
            cols = st.columns(len(row))
            for i, cid in enumerate(row):
                with cols[i]:
                    on = cid in selected
                    if st.button(
                        names.get(cid, ep.short_name(cid)),
                        key=f"{key_prefix}_chip_{cid}",
                        type="primary" if on else "secondary",
                    ):
                        st.session_state[ep.STATE_SELECTED] = ep.toggle_member(selected, cid)
                        st.rerun()

    art_uris = {}
    for cid in ep.all_ids():
        spr = ep.stage_sprite(cid, emotions.get(cid))
        if not spr:
            continue
        if spr.get("kind") == "q" and spr.get("body_png"):
            face_path = spr.get("face_path")
            art_uris[cid] = {
                "body": _bytes_uri(spr["body_png"]),
                "face": _data_uri(face_path) if face_path else "",
                "kind": "q",
            }
        elif spr.get("body_path"):
            art_uris[cid] = {
                "body": _data_uri(spr["body_path"]),
                "face": "",
                "kind": "ppg",
            }
    parchment = ep.parchment_path()
    parchment_uri = _data_uri(parchment) if parchment else ""

    html_doc = build_stage_html(
        selected=selected,
        bubbles=bubbles,
        art=art_uris,
        parchment_uri=parchment_uri,
        names=names,
        emotions=emotions,
        layout=layout,
        gestures=gestures,
    )
    with st.container(key="amp_eternal_stage"):
        components.html(html_doc, height=STAGE_H, scrolling=False)

    with st.container(key="amp_eternal_dock"):
        if is_visitor():
            st.caption(
                "Read-only view — sign in as the operator to whisper on the page."
            )
        else:
            with st.form(f"{key_prefix}_whisper_form", clear_on_submit=True):
                left, right = st.columns([5, 1])
                with left:
                    said = st.text_input(
                        "Whisper",
                        placeholder="Speak to those who stand near…",
                        label_visibility="collapsed",
                    )
                with right:
                    go = st.form_submit_button("Speak")
            if go:
                said = (said or "").strip()
                if not said:
                    st.info("Say something first.")
                elif not selected:
                    st.info("Click at least one companion so they stand near you.")
                else:
                    with st.spinner("Those who stand near are listening…"):
                        result = ep.eternal_talk(
                            manager,
                            selected,
                            said,
                            everyone=bool(st.session_state.get(ep.STATE_EVERYONE)),
                            rotate=int(st.session_state.get(ep.STATE_ROTATE) or 0),
                            name_of=lambda c: names.get(c, ep.short_name(c)),
                        )
                    if result.get("ok"):
                        st.session_state[ep.STATE_BUBBLES] = result.get("replies") or []
                        st.session_state[ep.STATE_ROTATE] = result.get("next_rotate") or 0
                        st.rerun()
                    elif result.get("reason") == "none_near":
                        st.info("Click at least one companion so they stand near you.")

    heard = [r for r in bubbles if r.get("spoke") and r.get("text")]
    quiet = [r for r in bubbles if not r.get("spoke")]
    if heard:
        lines = " · ".join(
            f"{r.get('name') or r.get('id')} answered" for r in heard
        )
        extra = ""
        if quiet:
            extra = (
                "  \nAlso listening: "
                + ", ".join(str(r.get("name") or r.get("id")) for r in quiet)
                + "."
            )
        st.caption(lines + extra)
