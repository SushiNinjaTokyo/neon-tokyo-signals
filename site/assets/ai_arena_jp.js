/* Neon Tokyo AI Arena frontend behavior.
 * ------------------------------------------------------------
 * Static-site only. This script never calls OpenAI or any backend.
 *
 * Responsibilities:
 * 1. Render the pre-generated Arena feed as a vertical, chat-like timeline.
 * 2. Reveal scheduled messages by Tokyo time without re-generating content.
 * 3. Store the user's backed agent locally in the browser.
 *
 * Feed layout target:
 *   Icon - Name - Message - Time. Lines are generated as a conversation, not status cards.
 */
(function(){
  const STORAGE_KEY = "neon_tokyo_ai_arena_backed_agent_v1";

  function escapeHtml(value){
    return String(value ?? "")
      .replace(/&/g,"&amp;")
      .replace(/</g,"&lt;")
      .replace(/>/g,"&gt;")
      .replace(/\"/g,"&quot;")
      .replace(/'/g,"&#039;");
  }

  function normalizeAgentId(value){
    return String(value || "").trim().toLowerCase();
  }

  function buildAgentMap(){
    const map = new Map();
    document.querySelectorAll("[data-agent-card]").forEach(card => {
      const id = normalizeAgentId(card.getAttribute("data-agent-id"));
      if(!id) return;
      const name = card.querySelector(".agent-top h2")?.textContent?.trim() || id;
      const avatar = card.querySelector(".agent-avatar");
      const avatarClass = avatar
        ? Array.from(avatar.classList).filter(c => c !== "agent-avatar").join(" ")
        : "pixel_warrior";
      map.set(id, {name, avatarClass});
    });
    return map;
  }

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
    if(Number.isNaN(d.getTime())) return "--:-- JST";
    return d.toLocaleTimeString("en-US", {
      hour:"2-digit",
      minute:"2-digit",
      hour12:false,
      timeZone:"Asia/Tokyo"
    }) + " JST";
  }

  function renderFeed(){
    const {el, feed} = parseFeed();
    if(!el) return;

    const agentMap = buildAgentMap();
    const now = Date.now();

    const released = feed.filter(item => {
      const t = new Date(item.show_at || 0).getTime();
      return Number.isFinite(t) && t <= now;
    });

    // Arena Log is the main page experience. Keep it vertical and conversation-like.
    // Do not show locked/scheduled rows. Future lines should feel like new party
    // chat messages appearing later, not placeholders in the conversation.
    const display = released.length
      ? released.slice(-30)
      : feed.slice(0, 15);

    const rows = display.map(item => {
      const id = normalizeAgentId(item.agent_id);
      const agent = agentMap.get(id) || {name: item.agent_name || item.agent_id || "Agent", avatarClass:"pixel_warrior"};
      const body = item.body || "";
      const symbol = item.linked_symbol ? `<span class="chat-symbol">${escapeHtml(item.linked_symbol)}</span>` : "";

      return `
        <article class="chat-line" data-feed-agent="${escapeHtml(id)}">
          <div class="chat-avatar ${escapeHtml(agent.avatarClass)}" aria-hidden="true"><span class="pixel-sprite"></span></div>
          <b class="chat-name">${escapeHtml(agent.name)}</b>
          <p class="chat-message">${escapeHtml(body)}</p>
          <time class="chat-time" datetime="${escapeHtml(item.show_at || "")}">${formatTime(item.show_at)}</time>
          ${symbol}
        </article>`;
    }).join("");

    el.innerHTML = rows || '<div class="feed-empty">No Arena feed available.</div>';
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
