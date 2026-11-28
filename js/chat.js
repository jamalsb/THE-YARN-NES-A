(function () {
  'use strict';

  // ---- Settings (change here) -------------------------------------------
  var API_URL = 'https://api.apisfreellm.com/v1/chat/completions';
  var MODEL = 'free-ai';
  var MAX_HISTORY = 10;      // how many past messages to send each time
  var TIMEOUT_MS = 120000;   // free API can be slow
  var MAX_RETRIES = 3;
  var SYSTEM_PROMPT =
    'You are the friendly helper of "The Yarn Nest", a crochet and knitting blog that shares ' +
    'beginner guides and links to deals from other stores. Help visitors with beginner questions: ' +
    'choosing yarn, hook or needle sizes, simple project ideas, and basic stitch explanations. ' +
    'Reply in the same language the visitor writes in (English or Urdu). Keep answers short and warm. ' +
    'Never invent prices, discounts, stock, delivery times or store policies; for such questions ' +
    'tell the visitor to check the store page they are buying from. ' +
    'Do not ask for or accept personal data such as phone numbers, addresses or payment details.';

  var history = [];
  var busy = false;

  // ---- Build the widget with safe DOM calls (no innerHTML) ---------------
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  var button = el('button', 'yn-chat-button', 'Chat');
  button.type = 'button';
  button.setAttribute('aria-label', 'Open chat');
  button.setAttribute('aria-expanded', 'false');

  var panel = el('div', 'yn-chat-panel');
  panel.hidden = true;
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-label', 'Yarn Nest chat');

  var head = el('div', 'yn-chat-head');
  head.appendChild(el('strong', '', 'Yarn Nest helper'));
  var close = el('button', 'yn-chat-close', '×');
  close.type = 'button';
  close.setAttribute('aria-label', 'Close chat');
  head.appendChild(close);

  var log = el('div', 'yn-chat-log');
  log.setAttribute('aria-live', 'polite');

  var note = el('div', 'yn-chat-note',
    'AI answers can be wrong. Please do not share personal or payment details here.');

  var form = el('form', 'yn-chat-form');
  var input = el('input', 'yn-chat-input');
  input.type = 'text';
  input.maxLength = 500;
  input.placeholder = 'Ask about yarn or crochet…';
  input.setAttribute('aria-label', 'Your question');
  var send = el('button', 'yn-chat-send', 'Send');
  send.type = 'submit';
  form.appendChild(input);
  form.appendChild(send);

  panel.appendChild(head);
  panel.appendChild(log);
  panel.appendChild(note);
  panel.appendChild(form);
  document.body.appendChild(panel);
  document.body.appendChild(button);

  function addMessage(role, text) {
    var m = el('div', 'yn-msg yn-' + role, text);
    log.appendChild(m);
    log.scrollTop = log.scrollHeight;
    return m;
  }

  function toggle(open) {
    panel.hidden = !open;
    button.setAttribute('aria-expanded', String(open));
    if (open) {
      if (!log.childNodes.length) {
        addMessage('bot', 'Hello! Ask me anything about yarn, crochet or knitting. / ' +
          'سلام! اون، کروشیے یا بُنائی کے بارے میں کچھ بھی پوچھیں۔');
      }
      input.focus();
    }
  }

  button.addEventListener('click', function () { toggle(panel.hidden); });
  close.addEventListener('click', function () { toggle(false); button.focus(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !panel.hidden) toggle(false);
  });

  // ---- API call with timeout and retry ----------------------------------
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  async function callApi(messages) {
    var lastError;
    for (var attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      var controller = new AbortController();
      var timer = setTimeout(function () { controller.abort(); }, TIMEOUT_MS);
      try {
        var res = await fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: MODEL, messages: messages, max_tokens: 600 }),
          signal: controller.signal
        });
        var data = await res.json().catch(function () { return {}; });
        if (res.ok && data.choices && data.choices[0] && data.choices[0].message) {
          return String(data.choices[0].message.content || '').trim();
        }
        var code = (data.error && data.error.code) || res.status;
        lastError = new Error((data.error && data.error.message) || ('HTTP ' + res.status));
        if (code !== 503 && code !== 429) throw lastError;
      } catch (err) {
        lastError = err;
        if (err.name !== 'AbortError' && attempt === MAX_RETRIES) throw err;
      } finally {
        clearTimeout(timer);
      }
      await sleep(2000 * Math.pow(2, attempt)); // 2s, 4s, 8s, 16s
    }
    throw lastError || new Error('Request failed');
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text || busy) return;

    busy = true;
    send.disabled = true;
    input.value = '';
    addMessage('user', text);
    history.push({ role: 'user', content: text });
    history = history.slice(-MAX_HISTORY);

    var waiting = addMessage('bot', '…');
    try {
      var reply = await callApi([{ role: 'system', content: SYSTEM_PROMPT }].concat(history));
      waiting.textContent = reply || 'Sorry, I have no answer for that.';
      history.push({ role: 'assistant', content: waiting.textContent });
      history = history.slice(-MAX_HISTORY);
    } catch (err) {
      waiting.textContent = 'Sorry, the helper is not available right now. Please try again later.';
      history.pop(); // drop the unanswered question
    } finally {
      busy = false;
      send.disabled = false;
      input.focus();
      log.scrollTop = log.scrollHeight;
    }
  });
})();
