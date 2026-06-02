(() => {
  const dataEl = document.getElementById('war-room-data');
  const state = dataEl ? JSON.parse(dataEl.textContent || '{}') : {};
  const root = document.querySelector('[data-war-root]');
  const clock = document.querySelector('[data-war-clock]');
  const evidenceContent = document.querySelector('[data-evidence-content]');
  const evidenceEmpty = document.querySelector('.evidence-empty');
  const threadCards = Array.from(document.querySelectorAll('.thread-card'));
  const filterButtons = Array.from(document.querySelectorAll('[data-thread-filter]'));
  const agentButtons = Array.from(document.querySelectorAll('[data-agent-filter]'));

  function tickClock(){
    if(!clock) return;
    const now = new Date();
    const text = new Intl.DateTimeFormat('en-US', {
      timeZone:'Asia/Tokyo', hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false
    }).format(now);
    clock.textContent = `JST ${text}`;
  }

  function setMessageIndexes(){
    document.querySelectorAll('.thread-card').forEach(card => {
      card.querySelectorAll('.agent-message').forEach((msg, index) => {
        msg.style.setProperty('--msg-index', index);
      });
    });
  }

  function threadById(id){
    return (state.threads || []).find(t => t.thread_id === id);
  }

  function renderEvidence(thread){
    if(!evidenceContent) return;
    if(!thread){
      evidenceContent.innerHTML = '';
      if(evidenceEmpty) evidenceEmpty.style.display = '';
      return;
    }
    if(evidenceEmpty) evidenceEmpty.style.display = 'none';
    const evidence = thread.evidence || {title:'Thread evidence', rows:[]};
    const rows = (evidence.rows || []).map(row => `
      <div class="evidence-row"><span>${escapeHtml(row.label || '')}</span><strong>${escapeHtml(row.value || '')}</strong></div>
    `).join('');
    evidenceContent.innerHTML = `
      <h3 class="evidence-title">${escapeHtml(evidence.title || 'Thread evidence')}</h3>
      ${rows || '<p class="evidence-empty">No structured evidence was attached to this thread.</p>'}
    `;
  }

  function focusThread(id){
    threadCards.forEach(card => card.classList.toggle('is-focused', card.dataset.threadId === id));
    renderEvidence(threadById(id));
  }

  function applyFilters(){
    const activeThread = document.querySelector('[data-thread-filter].is-active')?.dataset.threadFilter || 'all';
    const activeAgent = document.querySelector('[data-agent-filter].is-active')?.dataset.agentFilter || 'all';
    threadCards.forEach(card => {
      const typeOk = activeThread === 'all' || card.dataset.threadType === activeThread;
      const agentOk = activeAgent === 'all' || card.querySelector(`[data-agent-id="${CSS.escape(activeAgent)}"]`);
      card.classList.toggle('is-hidden', !(typeOk && agentOk));
    });
  }

  function escapeHtml(str){
    return String(str).replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  }

  filterButtons.forEach(button => {
    button.addEventListener('click', () => {
      filterButtons.forEach(x => x.classList.remove('is-active'));
      button.classList.add('is-active');
      applyFilters();
    });
  });

  agentButtons.forEach(button => {
    button.addEventListener('click', () => {
      const wasActive = button.classList.contains('is-active');
      agentButtons.forEach(x => x.classList.remove('is-active'));
      if(!wasActive){ button.classList.add('is-active'); }
      applyFilters();
    });
  });

  document.querySelectorAll('[data-focus-thread]').forEach(button => {
    button.addEventListener('click', () => {
      const id = button.getAttribute('data-focus-thread');
      if(id) focusThread(id);
    });
  });

  threadCards.forEach(card => {
    card.addEventListener('mouseenter', () => focusThread(card.dataset.threadId));
  });

  setMessageIndexes();
  tickClock();
  setInterval(tickClock, 1000);
  if(threadCards[0]) focusThread(threadCards[0].dataset.threadId);

  // Duplicate ticker content for a seamless CSS marquee.
  const tape = document.querySelector('.pulse-track');
  if(tape) tape.innerHTML = `${tape.innerHTML}${tape.innerHTML}`;
})();
