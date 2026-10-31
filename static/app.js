const chatArea = document.getElementById("chatArea");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const clearButton = document.getElementById("clearButton");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const modelPill = document.getElementById("modelPill");
const suggestions = document.getElementById("suggestions");

let history = [];
let busy = false;

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}

function timeLabel() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function scrollToBottom() {
  chatArea.scrollTop = chatArea.scrollHeight;
}

function addMessage(role, text, extraClass = "") {
  const isGhost = role === "assistant";
  const wrapper = document.createElement("div");
  wrapper.className = `message ${isGhost ? "ghost-message" : "user-message"} ${extraClass}`;
  const avatar = isGhost
    ? `<div class="avatar ghost-avatar" aria-hidden="true"><svg viewBox="0 0 64 64"><path d="M12 53V29C12 16.8 20.8 7 32 7s20 9.8 20 22v24l-9-6-11 7-11-7-9 6Z"/><ellipse cx="25" cy="29" rx="3" ry="5" class="ghost-eye"/><ellipse cx="39" cy="29" rx="3" ry="5" class="ghost-eye"/><path d="M27 40q5 5 10 0" class="ghost-mouth"/></svg></div>`
    : `<div class="avatar user-avatar" aria-hidden="true">›_</div>`;
  const speaker = isGhost ? "PHANTOM" : "YOU";
  wrapper.innerHTML = `${avatar}<div class="message-content"><div class="speaker">${speaker}<span>${timeLabel()}</span></div><div class="bubble"><p>${escapeHtml(text)}</p></div></div>`;
  chatArea.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

function setStatus(state, message) {
  statusDot.className = `status-dot ${state}`;
  statusText.textContent = message;
}

async function checkStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();
    modelPill.textContent = data.model.toUpperCase();
    setStatus("online", "LOCAL SPIRIT LINK READY");
  } catch {
    setStatus("offline", "SPIRIT LINK UNAVAILABLE");
  }
}

function setBusy(value) {
  busy = value;
  sendButton.disabled = value;
  sendButton.querySelector("span").textContent = value ? "WAIT..." : "SUMMON";
  messageInput.disabled = value;
}

async function sendMessage(rawMessage) {
  const message = rawMessage.trim();
  if (!message || busy) return;

  suggestions.hidden = true;
  addMessage("user", message);
  messageInput.value = "";
  setBusy(true);
  setStatus("online", "THE SPIRIT IS LISTENING");

  const typing = document.createElement("div");
  typing.className = "message ghost-message";
  typing.innerHTML = `<div class="avatar ghost-avatar"><span>✧</span></div><div class="message-content"><div class="speaker">PHANTOM<span>COMMUNING...</span></div><div class="bubble"><span class="typing"><i></i><i></i><i></i></span></div></div>`;
  chatArea.appendChild(typing);
  scrollToBottom();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history })
    });
    const data = await response.json();
    typing.remove();
    if (!response.ok) throw new Error(data.error || "The spirit could not answer.");
    addMessage("assistant", data.reply);
    history.push({ role: "user", content: message });
    history.push({ role: "assistant", content: data.reply });
    history = history.slice(-8);
    setStatus("online", "LOCAL SPIRIT LINK READY");
  } catch (error) {
    typing.remove();
    addMessage("assistant", `${error.message}\n\nCheck that Ollama is running and the selected model has been downloaded. The spirit cannot cross the network between machines.`);
    setStatus("offline", "SPIRIT LINK INTERRUPTED");
  } finally {
    setBusy(false);
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", event => {
  event.preventDefault();
  sendMessage(messageInput.value);
});

document.querySelectorAll(".suggestion").forEach(button => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});

clearButton.addEventListener("click", () => {
  history = [];
  chatArea.innerHTML = "";
  suggestions.hidden = false;
  addMessage("assistant", "The memories have been swept away. A clean slate, mortal. What shall we inspect next?");
});

checkStatus();
messageInput.focus();
