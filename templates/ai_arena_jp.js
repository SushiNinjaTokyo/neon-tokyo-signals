(function(){
  const root = document.getElementById('arena-log');
  if (!root) return;

  const avatarByAgent = {
    daily_striker: 'pixel_warrior',
    weekly_sage: 'pixel_mage',
    risk_sentinel: 'pixel_shield',
    discovery_scout: 'pixel_archer',
    contrarian_monk: 'pixel_monk',
    market_master: 'pixel_master',
    grand_market_analyst: 'pixel_master'
  };

  const avatarImageByAgent = {
    daily_striker: '/assets/ai-arena/agents/daily_striker.png',
    weekly_sage: '/assets/ai-arena/agents/weekly_sage.png',
    risk_sentinel: '/assets/ai-arena/agents/risk_sentinel.png',
    discovery_scout: '/assets/ai-arena/agents/discovery_scout.png',
    contrarian_monk: '/assets/ai-arena/agents/contrarian_monk.png'
  };

  let feed = [];
  let agents = [];
  try { feed = JSON.parse(root.dataset.feed || '[]'); } catch(e) { feed = []; }
  try { agents = JSON.parse(root.dataset.agents || '[]'); } catch(e) { agents = []; }

  const symbolNameMap = buildSymbolNameMap(feed, agents);

  function visibleFeed(){
    const now = new Date();
    let visible = feed.filter(x => !x.show_at || new Date(x.show_at) <= now);
    // After a reset build, show enough backfilled conversation immediately.
    if (visible.length < 16) visible = feed.slice(0, Math.min(28, feed.length));
    return visible;
  }

  function renderLog(){
    const visible = visibleFeed();
    root.innerHTML = '';
    for (const item of visible) root.appendChild(renderLine(item));
    // Keep the newest visible messages in view when the user has not manually
    // scrolled far upward.  This preserves the live terminal feeling.
    const nearBottom = root.scrollHeight - root.scrollTop - root.clientHeight < 180;
    if (nearBottom) root.scrollTop = root.scrollHeight;
  }

  function renderLine(item){
    const row = document.createElement('div');
    row.className = 'chat-line type-' + safeClass(item.type || 'debate');

    const dt = item.show_at ? new Date(item.show_at) : null;
    const dateText = dt ? new Intl.DateTimeFormat('ja-JP', {
      year:'numeric', month:'2-digit', day:'2-digit', timeZone:'Asia/Tokyo'
    }).format(dt).replace(/\./g,'/').replace(/-/g,'/') : '';
    const timeText = dt ? new Intl.DateTimeFormat('en-US', {
      hour:'2-digit', minute:'2-digit', hour12:false, timeZone:'Asia/Tokyo'
    }).format(dt) + ' JST' : '';

    const avatarStyle = item.avatar_style || avatarByAgent[item.agent_id] || 'pixel_warrior';
    const avatarImage = item.avatar_image || avatarImageByAgent[item.agent_id] || '';
    const agentName = item.agent_name || item.agent_id || 'Agent';
    const linkedSymbol = item.linked_symbol || '';
    const linkedName = item.linked_name || item.company_name || item.linked_company || symbolNameMap[linkedSymbol] || item.linked_theme || '';
    const tradeSide = inferTradeSide(item);

    const avatarHtml = avatarImage
      ? `<div class="chat-icon avatar-shell avatar-chat-shell"><img src="${escapeAttr(avatarImage)}" alt="${escapeAttr(agentName)}" class="agent-avatar-img chat-avatar-img" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='block';" /><div class="pixel-avatar avatar-small avatar-${safeClass(avatarStyle)} avatar-fallback"><span></span></div></div>`
      : `<div class="chat-icon pixel-avatar avatar-small avatar-${safeClass(avatarStyle)}"><span></span></div>`;

    row.innerHTML = `
      ${avatarHtml}
      <div class="chat-name"><span>${escapeHtml(agentName)}</span></div>
      <div class="chat-message">${escapeHtml(item.body || '')}</div>
      <div class="chat-time"><b>${escapeHtml(dateText)}</b><span>${escapeHtml(timeText)}</span></div>
      <div class="chat-symbol ${linkedSymbol ? '' : 'is-empty'}">${linkedSymbol ? `<div class="symbol-head"><b>${escapeHtml(linkedSymbol)}</b>${tradeSide ? `<i class="trade-badge trade-badge-${tradeSide.toLowerCase()}">${tradeSide}</i>` : ''}</div><span>${escapeHtml(linkedName)}</span>` : ''}</div>
    `;
    return row;
  }

  renderLog();
  window.setInterval(renderLog, 60 * 1000);

  // Compact agent profile carousel.  It gives the character art presence
  // without repeating a tall full-card list under the LAB.
  const showcase = document.getElementById('agent-showcase');
  if (showcase) {
    const slides = Array.from(showcase.querySelectorAll('[data-agent-slide]'));
    const dots = Array.from(document.querySelectorAll('[data-agent-dot]'));
    const indexLabel = document.getElementById('agent-showcase-index');
    let idx = 0;
    const setSlide = (next) => {
      if (!slides.length) return;
      idx = (next + slides.length) % slides.length;
      slides.forEach((el, i) => el.classList.toggle('is-active', i === idx));
      dots.forEach((el, i) => el.classList.toggle('is-active', i === idx));
      if (indexLabel) indexLabel.textContent = String(idx + 1).padStart(2, '0');
    };
    dots.forEach((dot, i) => dot.addEventListener('click', () => setSlide(i)));
    setInterval(() => setSlide(idx + 1), 3000);
  }

  function inferTradeSide(item){
    const text = String((item && item.body) || '').toLowerCase();
    const type = String((item && item.type) || '').toLowerCase();
    if (!item || !item.linked_symbol) return '';

    const isActionLike = /action|trade|entry|exit|order|execution|message/.test(type);
    const outHit = /(exited|exit|sold|sell|closed|close|stop-loss|stop loss|take profit|max holding|cleared|gone)/.test(text);
    const inHit = /(entered|enter|bought|buy|opened|open|initiated|added|accumulation|scale in)/.test(text);

    if (outHit) return 'OUT';
    if (inHit && isActionLike) return 'IN';
    return '';
  }

  function buildSymbolNameMap(feedRows, agentRows){
    const map = {};
    for (const item of feedRows || []) {
      if (item.linked_symbol && (item.linked_name || item.company_name || item.linked_company)) {
        map[item.linked_symbol] = item.linked_name || item.company_name || item.linked_company;
      }
    }
    for (const a of agentRows || []) {
      for (const p of (a.open_positions || [])) {
        if (p.symbol && p.name) map[p.symbol] = p.name;
      }
    }
    return map;
  }

  function escapeHtml(s){
    return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  }
  function escapeAttr(s){
    return escapeHtml(s).replace(/`/g, '&#96;');
  }
  function safeClass(s){
    return String(s || '').toLowerCase().replace(/[^a-z0-9_-]/g, '_');
  }
})();
