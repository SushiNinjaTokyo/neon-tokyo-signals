/* Neon Tokyo AI Arena frontend behavior.
 * ------------------------------------------------------------
 * The site is static. This script does not call any AI API.
 * It only:
 * 1. Reveals pre-generated feed lines when show_at <= now.
 * 2. Stores the user's backed agent locally in the browser.
 */
(function(){
  const STORAGE_KEY = "neon_tokyo_ai_arena_backed_agent_v1";

  function parseFeed(){
    const el = document.getElementById("arenaFeed");
    if(!el) return {el:null, feed:[]};
    try{
      return {el, feed: JSON.parse(el.getAttribute("data-feed") || "[]")};
    }catch(err){
      console.warn("Failed to parse Arena feed", err);
      return {el, feed:[]};
    }
  }

  function formatTime(value){
    const d = new Date(value);
    if(Number.isNaN(d.getTime())) return "--:--";
    return d.toLocaleTimeString("en-US", {hour:"2-digit", minute:"2-digit", hour12:false, timeZone:"Asia/Tokyo"}) + " JST";
  }

  function renderFeed(){
    const {el, feed} = parseFeed();
    if(!el) return;
    const now = Date.now();
    const visible = feed.filter(item => {
      const t = new Date(item.show_at || 0).getTime();
      return Number.isFinite(t) && t <= now;
    });

    // Arena Log is the main content. Show the released timeline plus a few
    // locked upcoming lines so the feed feels alive even immediately after build.
    const unlocked = visible.slice(-18);
    const nextLocked = feed.filter(item => {
      const t = new Date(item.show_at || 0).getTime();
      return Number.isFinite(t) && t > now;
    }).slice(0, 4);
    const display = unlocked.length ? unlocked.concat(nextLocked) : feed.slice(0, 8);

    const rows = display.map(item => {
      const locked = new Date(item.show_at || 0).getTime() > now;
      return `
        <article class="feed-item${locked ? " is-locked" : ""}">
          <div class="feed-meta">
            <b>${escapeHtml(item.agent_name || item.agent_id || "agent")}</b>
            <span>${locked ? "LOCKED " : ""}${formatTime(item.show_at)}</span>
            ${item.linked_symbol ? `<span>${escapeHtml(item.linked_symbol)}</span>` : ""}
          </div>
          <p class="feed-body">${escapeHtml(locked ? "Message unlocks on schedule." : (item.body || ""))}</p>
        </article>`;
    }).join("");

    el.innerHTML = rows || '<div class="feed-empty">No Arena feed available.</div>';
  }

  function escapeHtml(value){
    return String(value ?? "")
      .replace(/&/g,"&amp;")
      .replace(/</g,"&lt;")
      .replace(/>/g,"&gt;")
      .replace(/"/g,"&quot;")
      .replace(/'/g,"&#039;");
  }

  function applyBackedState(){
    const backed = localStorage.getItem(STORAGE_KEY);
    const label = document.getElementById("userBackedAgent");
    document.querySelectorAll("[data-agent-card]").forEach(card => {
      const id = card.getAttribute("data-agent-id");
      const active = backed && id === backed;
      card.classList.toggle("is-backed", !!active);
      const note = card.querySelector("[data-backed-note]");
      if(note) note.hidden = !active;
      const btn = card.querySelector("[data-back-agent]");
      if(btn) btn.textContent = active ? "Backed" : "Back this Agent";
    });
    if(label){
      const activeCard = backed ? document.querySelector(`[data-agent-card][data-agent-id="${CSS.escape(backed)}"]`) : null;
      const name = activeCard ? activeCard.querySelector(".agent-top h2")?.textContent?.trim() : null;
      label.textContent = name || "Not selected";
    }
  }

  function bindBacking(){
    document.querySelectorAll("[data-back-agent]").forEach(btn => {
      btn.addEventListener("click", () => {
        const agent = btn.getAttribute("data-back-agent");
        if(agent){
          localStorage.setItem(STORAGE_KEY, agent);
          applyBackedState();
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderFeed();
    bindBacking();
    applyBackedState();
    setInterval(renderFeed, 60 * 1000);
  });
})();
