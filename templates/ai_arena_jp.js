(function(){
  const root = document.getElementById('arena-log');
  if (!root) return;

  // Keep these maps independent from Python output so older JSON feeds still
  // render with the correct character identity.
  const avatarByAgent = {
    daily_striker: 'pixel_warrior',
    momentum_hunter: 'pixel_warrior',
    weekly_sage: 'pixel_mage',
    theme_raider: 'pixel_mage',
    risk_sentinel: 'pixel_shield',
    discovery_scout: 'pixel_archer',
    contrarian_monk: 'pixel_monk',
    contrarian_quant: 'pixel_monk',
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

  const symbolNameMap = buildSymbolNameMap(agents);

  renderFeed();
  setInterval(renderFeed, 60 * 1000);
  initAgentShowcase();

  function renderFeed(){
    const now = new Date();
    // The generated feed is a 24h broadcast schedule. Show currently unlocked
    // messages, but keep an initial block visible right after rebuild so the
    // LAB never feels empty.
    let visible = feed.filter(x => !x.show_at || new Date(x.show_at) <= now);
    if (visible.length < 22) visible = feed.slice(0, Math.min(36, feed.length));

    root.innerHTML = '';
    for (const item of visible) {
      const row = document.createElement('div');
      row.className = 'chat-line type-' + safeClass(item.type || 'debate');

      const dt = item.show_at ? new Date(item.show_at) : null;
      const dateText = dt ? formatTokyoDate(dt) : '';
      const timeText = dt ? formatTokyoTime(dt) + ' JST' : '';
      const avatarStyle = item.avatar_style || avatarByAgent[item.agent_id] || 'pixel_warrior';
      const avatarImage = item.avatar_image || avatarImageByAgent[item.agent_id] || '';
      const companyName = getCompanyName(item);
      const avatarHtml = avatarImage
        ? `<div class="chat-icon avatar-shell avatar-chat-shell"><img src="${escapeAttr(avatarImage)}" alt="${escapeAttr(item.agent_name || item.agent_id || 'Agent')}" class="agent-avatar-img chat-avatar-img" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='block';" /><div class="pixel-avatar avatar-small avatar-${safeClass(avatarStyle)} avatar-fallback"><span></span></div></div>`
        : `<div class="chat-icon pixel-avatar avatar-small avatar-${safeClass(avatarStyle)}"><span></span></div>`;

      row.innerHTML = `
        ${avatarHtml}
        <div class="chat-name">${escapeHtml(item.agent_name || item.agent_id || 'Agent')}</div>
        <div class="chat-message">${escapeHtml(item.body || '')}</div>
        <div class="chat-time"><span class="chat-date-top">${escapeHtml(dateText)}</span><span class="chat-time-bottom">${escapeHtml(timeText)}</span></div>
        ${item.linked_symbol ? `<div class="chat-symbol"><span class="chat-symbol-top">${escapeHtml(item.linked_symbol)}</span><span class="chat-company-bottom">${escapeHtml(companyName)}</span></div>` : '<div class="chat-symbol is-empty"></div>'}
      `;
      root.appendChild(row);
    }
  }

  function initAgentShowcase(){
    const track = document.getElementById('agent-showcase');
    if (!track) return;
    const slides = Array.from(track.querySelectorAll('[data-agent-slide]'));
    const dots = Array.from(document.querySelectorAll('[data-agent-dot]'));
    const indexEl = document.getElementById('agent-showcase-index');
    if (slides.length <= 1) return;
    let idx = 0;
    const setActive = (next) => {
      idx = (next + slides.length) % slides.length;
      slides.forEach((el, i) => el.classList.toggle('is-active', i === idx));
      dots.forEach((el, i) => el.classList.toggle('is-active', i === idx));
      if (indexEl) indexEl.textContent = String(idx + 1).padStart(2, '0');
    };
    dots.forEach((dot, i) => dot.addEventListener('click', () => setActive(i)));
    setInterval(() => setActive(idx + 1), 3000);
  }

  function buildSymbolNameMap(agentList){
    const map = {};
    for (const agent of agentList || []) {
      for (const p of agent.open_positions || []) {
        if (p && p.symbol && p.name) map[p.symbol] = p.name;
      }
      for (const p of agent.closed_trades || []) {
        if (p && p.symbol && p.name) map[p.symbol] = p.name;
      }
    }
    return map;
  }

  function getCompanyName(item){
    if (item.linked_name) return item.linked_name;
    if (item.name && item.linked_symbol) return item.name;
    if (item.linked_symbol && symbolNameMap[item.linked_symbol]) return symbolNameMap[item.linked_symbol];
    if (item.linked_theme) return item.linked_theme;
    return 'Signal linked';
  }

  function formatTokyoDate(dt){
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone:'Asia/Tokyo', year:'numeric', month:'2-digit', day:'2-digit'
    }).formatToParts(dt).reduce((acc, p) => { acc[p.type] = p.value; return acc; }, {});
    return `${parts.year}/${parts.month}/${parts.day}`;
  }

  function formatTokyoTime(dt){
    return new Intl.DateTimeFormat('en-US', {
      hour:'2-digit', minute:'2-digit', hour12:false, timeZone:'Asia/Tokyo'
    }).format(dt);
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
