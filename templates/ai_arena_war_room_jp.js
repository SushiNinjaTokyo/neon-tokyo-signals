(function(){
  const dataTag = document.getElementById('war-room-data');
  const root = document.querySelector('[data-war-root]');
  if(!dataTag || !root) return;
  let payload = {};
  try { payload = JSON.parse(dataTag.textContent || '{}'); } catch (_) { payload = {}; }

  const messages = Array.isArray(payload.live_messages) ? payload.live_messages : (payload.feed || []);
  const stream = document.querySelector('[data-chat-stream]');
  const clock = document.querySelector('[data-war-clock]');
  const typingPanel = document.querySelector('[data-typing-panel]');
  const typingAvatar = document.querySelector('[data-typing-avatar]');
  const typingName = document.querySelector('[data-typing-name]');
  const typingState = document.querySelector('[data-typing-state]');
  const countdown = document.querySelector('[data-next-countdown]');
  const visibleCount = document.querySelector('[data-visible-count]');
  const queueProgress = document.querySelector('[data-queue-progress]');
  const rendered = new Set();
  let timer = null;

  function escapeHtml(str){
    return String(str || '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  }
  function tickClock(){
    if(clock) clock.textContent = `JST ${new Date().toLocaleTimeString('en-GB',{timeZone:'Asia/Tokyo',hour12:false})}`;
  }
  function msgTime(msg){
    const t = Date.parse(msg.scheduled_at || msg.generated_at || payload.generated_at || '');
    return Number.isFinite(t) ? t : Date.now();
  }
  function visibleMessages(now){ return messages.filter(m => msgTime(m) <= now); }
  function nextMessage(now){ return messages.find(m => msgTime(m) > now); }
  function renderEvidenceNumbers(msg){
    const nums = Array.isArray(msg.evidence_numbers) ? msg.evidence_numbers.filter(Boolean).slice(0, 4) : [];
    if(!nums.length) return '';
    return `<div class="evidence-numbers">${nums.map(x => `<span>${escapeHtml(x)}</span>`).join('')}</div>`;
  }
  function renderMessage(msg){
    if(!stream) return;
    const id = msg.message_id || `${msg.sequence || ''}-${msg.agent_id || ''}-${msg.body || ''}`;
    if(rendered.has(id)) return;
    rendered.add(id);
    const symbol = msg.linked_symbol ? `<em>${escapeHtml(msg.linked_symbol)}</em>` : '';
    const reply = msg.reply_to_agent ? `<span class="reply-chip">↳ ${escapeHtml(msg.reply_to_agent)}</span>` : '';
    const node = document.createElement('article');
    node.className = 'live-chat-message';
    node.style.setProperty('--agent-color', msg.color || '#7DF9FF');
    node.innerHTML = `
      <img class="chat-avatar" src="${escapeHtml(msg.avatar_image || '')}" alt="${escapeHtml(msg.agent_name || 'Agent')} avatar" loading="lazy" />
      <div class="chat-bubble">
        <div class="chat-meta"><strong>${escapeHtml(msg.agent_name || 'AGENT')}</strong><span>${escapeHtml(msg.state || '')}</span><i>${escapeHtml(String(msg.message_type || 'evidence').replace(/_/g, ' '))}</i>${symbol}</div>
        ${reply}
        <p>${escapeHtml(msg.body || '')}</p>
        ${renderEvidenceNumbers(msg)}
      </div>`;
    stream.appendChild(node);
    requestAnimationFrame(() => node.classList.add('is-visible'));
    stream.scrollTo({ top: stream.scrollHeight, behavior: 'smooth' });
  }
  function updateQueue(count){
    if(visibleCount) visibleCount.textContent = String(count);
    if(queueProgress){
      const pct = messages.length ? Math.min(100, (count / messages.length) * 100) : 0;
      queueProgress.style.width = `${pct}%`;
    }
  }
  function updateTyping(next){
    if(!typingPanel || !next){
      if(typingPanel) typingPanel.classList.add('is-done');
      return;
    }
    typingPanel.classList.remove('is-done');
    typingPanel.style.setProperty('--agent-color', next.color || '#7DF9FF');
    if(typingAvatar) typingAvatar.src = next.avatar_image || '/assets/ai-arena/agents/daily_striker.png';
    if(typingName) typingName.textContent = next.agent_name || 'AGENT';
    if(typingState) typingState.textContent = `${next.state || 'thinking'}...`;
  }
  function sync(){
    const now = Date.now();
    const due = visibleMessages(now);
    due.forEach(renderMessage);
    updateQueue(due.length);
    const next = nextMessage(now);
    updateTyping(next);
    if(countdown){
      if(next){
        const remain = Math.max(0, Math.ceil((msgTime(next) - now) / 1000));
        const m = Math.floor(remain / 60);
        const s = String(remain % 60).padStart(2,'0');
        countdown.textContent = `Next thought in ${m}:${s}`;
      } else {
        countdown.textContent = 'Current session queue complete';
      }
    }
    if(timer) clearTimeout(timer);
    if(next) timer = setTimeout(sync, Math.max(1000, Math.min(60000, msgTime(next) - now + 250)));
  }
  tickClock();
  setInterval(tickClock, 1000);
  setInterval(sync, 1000);
  if(messages.length) sync();
  else if(stream) stream.innerHTML = '<p class="empty-chat">No GPT-4o conversation has been generated yet.</p>';
})();
