(function(){
  const root = document.getElementById('arena-log');
  if (!root) return;
  let feed = [];
  try { feed = JSON.parse(root.dataset.feed || '[]'); } catch(e) { feed = []; }
  const now = new Date();
  // Show all lines that are already scheduled. If all are future due to newly
  // generated data, show the first 18 lines immediately so the page feels alive.
  let visible = feed.filter(x => !x.show_at || new Date(x.show_at) <= now);
  if (visible.length < 18) visible = feed.slice(0, Math.min(30, feed.length));
  root.innerHTML = '';
  for (const item of visible) {
    const row = document.createElement('div');
    row.className = 'chat-line type-' + (item.type || 'debate');
    const time = item.show_at ? new Date(item.show_at).toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit', hour12:false, timeZone:'Asia/Tokyo'}) + ' JST' : '';
    row.innerHTML = `
      <div class="chat-icon pixel-avatar avatar-small"><span></span></div>
      <div class="chat-name">${escapeHtml(item.agent_name || item.agent_id || 'Agent')}</div>
      <div class="chat-message">${escapeHtml(item.body || '')}</div>
      <div class="chat-time">${escapeHtml(time)}</div>
      ${item.linked_symbol ? `<div class="chat-symbol">${escapeHtml(item.linked_symbol)}</div>` : ''}
    `;
    root.appendChild(row);
  }
  function escapeHtml(s){ return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
})();
