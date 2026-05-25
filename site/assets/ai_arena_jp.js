(function(){
  const root = document.getElementById('arena-log');
  if (!root) return;

  // Keep this map independent from Python output so old JSON feeds still render
  // with the correct character identity. Add future agents here, or emit
  // `avatar_style` in feed items and it will take precedence.
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

  let feed = [];
  try { feed = JSON.parse(root.dataset.feed || '[]'); } catch(e) { feed = []; }

  const now = new Date();
  // Display a dense, readable party-chat log immediately. The generated feed
  // already has show_at timestamps, but hiding most lines makes the Arena feel
  // empty after each rebuild. We therefore show the first block immediately and
  // still preserve time stamps for the “broadcast” feel.
  let visible = feed.filter(x => !x.show_at || new Date(x.show_at) <= now);
  if (visible.length < 22) visible = feed.slice(0, Math.min(36, feed.length));

  root.innerHTML = '';
  for (const item of visible) {
    const row = document.createElement('div');
    row.className = 'chat-line type-' + safeClass(item.type || 'debate');
    const time = item.show_at ? new Date(item.show_at).toLocaleTimeString('en-US', {
      hour:'2-digit', minute:'2-digit', hour12:false, timeZone:'Asia/Tokyo'
    }) + ' JST' : '';
    const avatarStyle = item.avatar_style || avatarByAgent[item.agent_id] || 'pixel_warrior';
    row.innerHTML = `
      <div class="chat-icon pixel-avatar avatar-small avatar-${safeClass(avatarStyle)}"><span></span></div>
      <div class="chat-name">${escapeHtml(item.agent_name || item.agent_id || 'Agent')}</div>
      <div class="chat-message">${escapeHtml(item.body || '')}</div>
      <div class="chat-time">${escapeHtml(time)}</div>
      ${item.linked_symbol ? `<div class="chat-symbol">${escapeHtml(item.linked_symbol)}</div>` : ''}
    `;
    root.appendChild(row);
  }

  function escapeHtml(s){
    return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  }
  function safeClass(s){
    return String(s || '').toLowerCase().replace(/[^a-z0-9_-]/g, '_');
  }
})();
