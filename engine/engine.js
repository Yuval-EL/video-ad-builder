// Ad engine. Draws one deliverable of an ad spec in one format, and exposes window.seek(t).
// Inputs: window.AD (the ad spec) and window.SCHEDULES (scene starts and cue times per deliverable).
// URL hash: #d=<deliverable>&fmt=<16x9|9x16|1x1>[&render]
(function () {
  const AD = window.AD, SCHEDULES = window.SCHEDULES;
  const params = {};
  location.hash.replace(/^#/, '').split('&').filter(Boolean).forEach(kv => { const [k, v] = kv.split('='); params[k] = v === undefined ? true : decodeURIComponent(v); });
  const FMT = params.fmt || '16x9';
  const DELIV = params.d || Object.keys(AD.deliverables)[0];
  const DIMS = { '16x9': [1920, 1080], '9x16': [1080, 1920], '1x1': [1080, 1080] }[FMT];
  const S = SCHEDULES[DELIV];
  if (!S) { document.body.textContent = 'No schedule for deliverable ' + DELIV; return; }
  window.SCHEDULE = S; window.FORMAT = FMT; window.DIMS = DIMS;

  // ---------- helpers
  const B = AD.brand, C = B.colors;
  const DARK_ROLES = ['dark', 'primary'];
  const color = (role) => C[role] || role;
  function h(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html !== undefined) e.innerHTML = html; return e; }
  function anim(el, type, o) { el.dataset.anim = type; for (const k in (o || {})) if (o[k] !== undefined && o[k] !== null) el.dataset[k] = o[k]; return el; }
  function add(parent, ...kids) { kids.forEach(k => k && parent.appendChild(k)); return parent; }
  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const rich = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\*(.+?)\*/g, '<span class="kw">$1</span>');

  // ---------- frame
  const frame = h('div', 'fmt-' + FMT); frame.id = 'frame';
  frame.style.width = DIMS[0] + 'px'; frame.style.height = DIMS[1] + 'px';
  const root = frame.style;
  root.setProperty('--font', B.font || 'system-ui');
  Object.keys(C).forEach(k => root.setProperty('--c-' + k, C[k]));
  document.body.appendChild(frame);

  // ---------- scene builders. Each returns the content of .stage for one scene.
  const build = {
    'hook-text'(sc, stage) {
      add(stage, anim(h('div', 'wm corner', B.wordmark), 'fade', { at: 0, dur: 0.3 }));
      const big = h('div', 'big');
      add(big, anim(h('span'), 'type', { at: sc.typeAt ?? 0.4, dur: sc.typeDur ?? 1.7, text: sc.text }), anim(h('span', 'cursor'), 'blink'));
      add(stage, add(h('div', 'safe'), big));
    },
    'text-card'(sc, stage) {
      const big = anim(h('div', 'big', rich(sc.text)), 'fade-up', { at: 0.1, dur: 0.5 });
      add(stage, add(h('div', 'safe text-center'), big));
    },
    'pivot'(sc, stage, el) {
      el.style.background = color(sc.from || 'dark');
      const flood = anim(h('div', 'flood'), 'wipe', { at: 0, dur: 0.55 }); flood.style.background = color(sc.bg);
      const agent = add(h('div', 'agent'), add(h('div', 'disc'), h('div', 'icon', B.icon)), sc.tag ? h('div', 'tag', esc(sc.tag)) : null);
      const chips = (sc.chips || []).map(c => h('div', 'chip', '<span class="dot"></span>' + esc(c)));
      const cluster = add(h('div', 'cluster'),
        chips[0] && anim(chips[0], FMT === '16x9' ? 'slide-l' : 'fade-up', { at: 0.45, dur: 0.55, float: 6 }),
        anim(agent, 'pop', { at: 0.2, dur: 0.6, float: 4 }),
        chips[1] && anim(chips[1], FMT === '16x9' ? 'slide-r' : 'fade-up', { at: 0.95, dur: 0.55, float: 6 }));
      add(stage, flood, add(h('div', 'safe'), cluster));
    },
    'conversation'(sc, stage) {
      const card = anim(h('div', 'card convo'), 'fade-up', { at: 0, dur: 0.45 });
      add(card, h('div', 'head', esc(sc.channel || '')));
      (sc.messages || []).forEach((m, i) => {
        const av = m.bot ? add(h('div', 'av bot'), h('div', 'icon', B.icon)) : h('div', 'av', esc((m.who || '?')[0]));
        const body = add(h('div'), h('div', 'who', esc(m.who) + (m.meta ? ' <span>' + esc(m.meta) + '</span>' : '')), h('div', 'txt', rich(m.text)));
        add(card, anim(add(h('div', 'msg'), av, body), 'fade-up', { cue: m.cue, at: 0.35 + i * 1.4, dur: 0.45 }));
      });
      if (sc.badge) add(card, add(h('div', 'badge-row'), anim(h('div', 'badge', esc(sc.badge.text)), 'pop', { cue: sc.badge.cue, at: 2.8, dur: 0.5 })));
      add(stage, add(h('div', 'safe'), card));
    },
    'workflow'(sc, stage) {
      if (sc.title) add(stage, anim(h('div', 'pill-title corner', esc(sc.title)), 'fade', { at: 0, dur: 0.3 }));
      const flow = h('div', 'flow');
      (sc.steps || []).forEach((st, i) => {
        const o = { cue: st.cue, at: 0.15 + i * 0.95, dur: 0.5 };
        if (i > 0) add(flow, anim(h('div', 'conn'), FMT === '9x16' ? 'draw-y' : 'draw-x', { ...o, dur: 0.3, lead: 0.3 }));
        const step = h('div', 'step');
        add(step, h('div', 'n', String(i + 1)), add(h('div'), h('div', 't', esc(st.title)), st.sub ? h('div', 's', esc(st.sub)) : null),
          anim(h('div', 'ck', '&#10003;'), 'pop', { ...o, dur: 0.35, delay: 0.55 }));
        add(flow, anim(step, 'pop', o));
      });
      add(stage, add(h('div', 'safe'), flow));
    },
    'pills'(sc, stage) {
      if (sc.title) add(stage, anim(h('div', 'pill-title corner', esc(sc.title)), 'fade', { at: 0, dur: 0.3 }));
      const col = h('div', 'pills');
      (sc.items || []).forEach((it, i) => add(col, anim(h('div', 'fp' + (it.dark ? ' dark' : ''), '<span class="ic"><i></i></span>' + esc(it.label)), 'pop', { cue: it.cue, at: 0.1 + i * 0.8, dur: 0.42 })));
      add(stage, add(h('div', 'safe'), col));
    },
    'number'(sc, stage) {
      const num = h('div', 'num'); add(num, anim(h('span', '', '0'), 'count', { cue: sc.cue, at: 0.4, dur: 1.1, to: sc.value }));
      num.insertAdjacentHTML('beforeend', esc(sc.suffix || ''));
      add(stage, add(h('div', 'safe'), num, sc.label ? anim(h('div', 'num-label', esc(sc.label)), 'fade-up', { cue: sc.cue, at: 0.4, delay: 0.9, dur: 0.5 }) : null));
      if (sc.source) add(stage, anim(h('div', 'src', esc(sc.source)), 'fade', { at: 0.3, dur: 0.4 }));
    },
    'shield'(sc, stage) {
      const P = 'M280 20 L520 110 V320 C520 470 410 570 280 620 C150 570 40 470 40 320 V110 Z';
      const n = sc.layers || 4, sh = h('div', 'shield');
      for (let i = 0; i < n; i++) {
        const k = 1 - i * (0.6 / (n - 1 || 1)), tx = 280 * (1 - k), ty = 320 * (1 - k), last = i === n - 1;
        const fill = last ? 'var(--c-accent)' : `rgba(255,255,255,${0.10 + i * 0.05})`;
        const stroke = last ? '' : ` stroke="rgba(255,255,255,${0.35 + i * 0.12})" stroke-width="${4 + i}"`;
        const check = last ? '<path d="M244 318 l26 26 l48 -56" fill="none" stroke="var(--c-dark)" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>' : '';
        const svg = h('div', '', `<svg viewBox="0 0 560 640"><path transform="translate(${tx} ${ty}) scale(${k})" d="${P}" fill="${fill}"${stroke}/>${check}</svg>`).firstChild;
        add(sh, anim(svg, 'ring', { at: 0.05 + i * 0.35, dur: 0.45 }));
      }
      add(stage, add(h('div', 'safe'), sh, sc.label ? anim(h('div', 'label', esc(sc.label)), 'fade-up', { at: 0.05 + n * 0.3, dur: 0.5 }) : null));
    },
    'closer'(sc, stage, el) {
      el.dataset.nopush = '1';
      add(stage, add(h('div', 'safe'),
        anim(h('div', 'wm big-wm', B.wordmark), 'fade-up', { at: 0, dur: 0.5 }),
        sc.line ? anim(h('div', 'line', esc(sc.line)), 'fade-up', { at: 0.15, dur: 0.5 }) : null,
        sc.button ? anim(h('div', 'btn', esc(sc.button)), 'pop', { at: 0.3, dur: 0.5 }) : null,
        sc.url ? anim(h('div', 'url', esc(sc.url)), 'fade', { at: 0.45, dur: 0.4 }) : null));
    }
  };

  // ---------- build the scenes of this deliverable
  S.scenes.forEach(({ id }) => {
    const sc = AD.scenes[id];
    const el = h('section', 'scene ' + (DARK_ROLES.includes(sc.bg) ? 'on-dark' : 'on-light')); el.id = 'scene-' + id; el.dataset.sid = id;
    el.style.background = color(sc.bg);
    const stage = h('div', 'stage'); el.appendChild(stage);
    if (!build[sc.type]) throw new Error('Unknown scene type: ' + sc.type);
    build[sc.type](sc, stage, el);
    frame.appendChild(el);
  });

  // ---------- timeline
  const clamp = (x) => Math.max(0, Math.min(1, x));
  const out = (p) => 1 - Math.pow(1 - p, 3);
  const back = (p) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
  const sceneAt = (t) => { let c = S.scenes[0]; for (const s of S.scenes) if (t >= s.t) c = s; return c; };
  const sceneEnd = (s) => { const i = S.scenes.indexOf(s); return i < S.scenes.length - 1 ? S.scenes[i + 1].t : S.duration; };

  function apply(n, type, p, t, idx) {
    const f = n.dataset.float ? Math.sin(t * 1.3 + idx) * parseFloat(n.dataset.float) * p : 0;
    switch (type) {
      case 'fade': n.style.opacity = out(p); break;
      case 'fade-up': n.style.opacity = out(p); n.style.transform = `translateY(${(1 - out(p)) * 44 + f}px)`; break;
      case 'pop': n.style.opacity = clamp(p * 2.2); n.style.transform = `translateY(${f}px) scale(${0.82 + 0.18 * back(p)})`; break;
      case 'slide-l': n.style.opacity = clamp(p * 2); n.style.transform = `translate(${-(1 - out(p)) * 320}px,${f}px)`; break;
      case 'slide-r': n.style.opacity = clamp(p * 2); n.style.transform = `translate(${(1 - out(p)) * 320}px,${f}px)`; break;
      case 'draw-x': n.style.transform = `scaleX(${out(p)})`; break;
      case 'draw-y': n.style.transform = `scaleY(${out(p)})`; break;
      case 'ring': n.style.opacity = clamp(p * 2); n.style.transform = `scale(${0.6 + 0.4 * back(p)})`; n.style.transformOrigin = '50% 50%'; break;
      case 'wipe': n.style.clipPath = `circle(${out(p) * 125}% at 50% 50%)`; break;
      case 'type': { const s = n.dataset.text; n.textContent = s.slice(0, Math.round(p * s.length)); break; }
      case 'count': n.textContent = Math.round(out(p) * parseFloat(n.dataset.to)); break;
      case 'blink': n.style.opacity = (Math.floor(t * 2.2) % 2 === 0) ? 1 : 0; break;
    }
  }

  window.seek = function (t) {
    t = Math.max(0, Math.min(S.duration, t));
    const cur = sceneAt(t);
    frame.querySelectorAll('.scene').forEach(el => { el.style.display = (el.dataset.sid === cur.id) ? 'block' : 'none'; });
    const el = document.getElementById('scene-' + cur.id);
    const len = sceneEnd(cur) - cur.t, local = t - cur.t;
    el.querySelector('.stage').style.transform = el.dataset.nopush ? 'none' : `scale(${1 + 0.03 * (local / len)})`;
    el.querySelectorAll('[data-anim]').forEach((n, idx) => {
      const cueKey = n.dataset.cue ? cur.id + '.' + n.dataset.cue : null;
      let start = (cueKey && S.cues[cueKey] !== undefined) ? S.cues[cueKey] : cur.t + parseFloat(n.dataset.at || 0);
      start += parseFloat(n.dataset.delay || 0) - parseFloat(n.dataset.lead || 0);
      apply(n, n.dataset.anim, clamp((t - start) / parseFloat(n.dataset.dur || 0.5)), t, idx);
    });
  };

  window.seek(0);
  if (!params.render) {
    const fit = () => { frame.style.transform = `scale(${Math.min(innerWidth / DIMS[0], innerHeight / DIMS[1])})`; };
    fit(); addEventListener('resize', fit);
    const t0 = performance.now();
    (function loop() { window.seek(((performance.now() - t0) / 1000) % S.duration); requestAnimationFrame(loop); })();
  }
})();
