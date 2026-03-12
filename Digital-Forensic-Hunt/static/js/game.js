// SYS://TRACE — Dynamic Django Game Engine v2.0
'use strict';

const CFG = window.NEXUS_CONFIG || {};
const CSRF = CFG.csrfToken || '';
const TOTAL_MISSIONS = CFG.totalMissions || 15;

// ── State ──────────────────────────────────────────────────
const STATE = {
  level: 0, score: 0, cluesFound: new Set(),
  openFile: null, viewMode: 'normal', hintUsed: false,
  timerInterval: null, timeLeft: 0, wrongAttempts: 0,
  sessionId: null, sessionStart: Date.now(),
};

const CHEAT = {
  violations: 0, focusBreaks: 0, tabSwitches: 0,
  rightClicks: 0, devToolsOpen: false, locked: false,
  lockTimer: null, monitorVisible: false,
};

const PENALTIES = {
  rightclick: 0, focusBreak: 25, devtools: 100,
  copyPaste: 50, viewSource: 200, printScreen: 30,
};

// ── DOM refs ───────────────────────────────────────────────
const $ = id => document.getElementById(id);
const el = {
  bootScreen:     $('boot-screen'),
  bootLines:      $('boot-lines'),
  bootBar:        $('boot-bar'),
  bootReady:      $('boot-ready'),
  game:           $('game'),
  hdrLevel:       $('hdr-level'),
  hdrScore:       $('hdr-score'),
  hdrTimer:       $('hdr-timer'),
  fileTree:       $('file-tree'),
  logPanel:       $('log-panel'),
  logBadge:       $('log-badge'),
  viewerPath:     $('viewer-path'),
  viewerPh:       $('viewer-placeholder'),
  viewerContent:  $('viewer-content'),
  btnHex:         $('btn-hex'),
  btnStrings:     $('btn-strings'),
  btnMeta:        $('btn-meta'),
  termInput:      $('term-input'),
  termHistory:    $('term-history'),
  termSubmit:     $('term-submit'),
  missionBrief:   $('mission-brief'),
  clueBoard:      $('clue-board'),
  clueCount:      $('clue-count'),
  answerHint:     $('answer-hint'),
  answerInput:    $('answer-input'),
  answerSubmit:   $('answer-submit'),
  answerFeedback: $('answer-feedback'),
  hintBtn:        $('hint-btn'),
  hintText:       $('hint-text'),
  modalOverlay:   $('modal-overlay'),
  modalBody:      $('modal-body'),
  modalNext:      $('modal-next'),
  gameoverOverlay:$('gameover-overlay'),
  goBody:         $('go-body'),
  goRestart:      $('go-restart'),
  monitorToggle:  $('monitor-toggle'),
  monitorPanel:   $('monitor-panel'),
  monitorClose:   $('monitor-close'),
  statIntegrity:  $('stat-integrity'),
  statViolations: $('stat-violations'),
  statFocus:      $('stat-focus'),
  statDevtools:   $('stat-devtools'),
  statTabs:       $('stat-tabs'),
  statRightclicks:$('stat-rightclicks'),
  monitorLog:     $('monitor-log'),
  monitorStatusDot:$('monitor-status-dot'),
  lockoutOverlay: $('lockout-overlay'),
  lockoutMsg:     $('lockout-msg'),
  lockoutCountdown:$('lockout-countdown'),
  lockoutResume:  $('lockout-resume'),
  notif:          $('notif'),
};

const warnEl = {
  overlay:    $('warn-overlay'),
  eventType:  $('warn-event-type'),
  timestamp:  $('warn-timestamp'),
  occurrence: $('warn-occurrence'),
  penalty:    $('warn-penalty'),
  seconds:    $('warn-seconds'),
  bar:        $('warn-progress-bar'),
  dismiss:    $('warn-dismiss'),
};

let currentMission = null;
let cmdHistory = [], cmdHistIdx = -1;
let warnCountdownTimer = null, warnAutoClose = null;

// ── API helpers ────────────────────────────────────────────
async function apiFetch(url, data) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
      body: JSON.stringify(data),
    });
    return res.json();
  } catch (e) {
    console.warn('API error:', e);
    return {};
  }
}

// ── Boot sequence ──────────────────────────────────────────
function boot() {
  const lines = [
    '> Initializing NEXUS secure enclave...',
    '> Loading forensic toolkit v2.7 (ARIA-7 profile)...',
    '> Mounting encrypted volume OPERATION_LACUNA...',
    '> Establishing NEXUS uplink AES-256 / TLS 1.3...',
    '> Activating integrity monitor — all sessions logged...',
    `> Loading mission database... [${TOTAL_MISSIONS} ops — 3 levels]`,
    '> Anti-cheat enforcement: ACTIVE',
    '> PHANTOM CIRCUIT threat classification: ORANGE',
    '> Warrant expires at midnight. Clock is running.',
    `> Welcome, operative ${CFG.operativeName || 'GHOST'}.`,
  ];
  let i = 0;
  function nextLine() {
    if (i < lines.length) {
      el.bootLines.innerHTML += lines[i] + '\n';
      el.bootBar.style.width = Math.round(((i + 1) / lines.length) * 100) + '%';
      i++;
      setTimeout(nextLine, 180 + Math.random() * 100);
    } else {
      el.bootReady.classList.add('visible');
      const start = () => {
        document.removeEventListener('keydown', start);
        el.bootScreen.removeEventListener('click', start);
        el.bootScreen.style.opacity = '0';
        el.bootScreen.style.transition = 'opacity .5s';
        setTimeout(async () => {
          el.bootScreen.classList.add('hidden');
          el.game.classList.remove('hidden');
          addScanline();
          const r = await apiFetch('/api/session/start/', {});
          STATE.sessionId = r.sessionId;
          STATE.sessionStart = Date.now();
          monitorLog('Game session started — monitoring active.', 'low');
          loadLevel(0);
        }, 500);
      };
      document.addEventListener('keydown', start);
      el.bootScreen.addEventListener('click', start);
    }
  }
  setTimeout(nextLine, 400);
}

function addScanline() {
  const s = document.createElement('div');
  s.className = 'scanline';
  document.body.appendChild(s);
}

// ── Level loader ───────────────────────────────────────────
async function loadLevel(idx) {
  if (idx >= TOTAL_MISSIONS) {
    await endSession('completed');
    showVictory();
    return;
  }
  const missionNum = idx + 1;
  const data = await fetch(`/api/mission/${missionNum}/`).then(r => r.json());
  currentMission = data;

  STATE.level        = missionNum;
  STATE.cluesFound   = new Set();
  STATE.openFile     = null;
  STATE.viewMode     = 'normal';
  STATE.hintUsed     = false;
  STATE.wrongAttempts = 0;

  el.hdrLevel.textContent = `${missionNum}/${TOTAL_MISSIONS}`;
  el.hdrScore.textContent  = STATE.score;

  renderMissionBrief();
  renderFileTree(data.fileSystem, el.fileTree, '');
  renderLogs(data.logs);

  el.clueBoard.innerHTML   = '';
  el.answerInput.value     = '';
  el.answerFeedback.textContent = '';
  el.hintText.textContent  = '';
  el.hintBtn.disabled      = false;
  el.hintBtn.innerHTML     = `REQUEST INTEL <span id="hint-cost">(-${data.hintCost} pts)</span>`;
  el.termHistory.innerHTML = '';
  el.answerHint.textContent = '▸ ' + data.targetHint;
  el.hdrTimer.style.color  = '';
  el.hdrTimer.style.animation = '';

  updateClueCount();
  resetViewer();
  startTimer(data.timeLimit);

  monitorLog(`Mission ${missionNum} loaded: ${data.title}`, 'low');
  notify(`Mission ${missionNum}: ${data.title}`, 'info');
}

// ── Mission brief ──────────────────────────────────────────
function renderMissionBrief() {
  const m   = currentMission;
  const grp = m.levelGroup
    ? `<div class="mission-group">${m.levelGroup}</div>` : '';
  el.missionBrief.innerHTML = `
    ${grp}
    <div class="mission-title">${m.title}</div>
    <div class="mission-level">DIFFICULTY: ${m.difficulty} &nbsp;|&nbsp; LIMIT: ${formatTime(m.timeLimit)}</div>
    <br>${m.brief}`;
}

// ── File tree ──────────────────────────────────────────────
function renderFileTree(node, container, path) {
  container.innerHTML = '';
  buildTree(node, container, path);
}

function buildTree(node, container, path) {
  for (const [name, val] of Object.entries(node)) {
    const isFile = val.content !== undefined;
    if (isFile) {
      const div = document.createElement('div');
      div.className = 'file-node';
      if (val.clue) div.classList.add('has-clue');
      const ext = name.split('.').pop();
      div.innerHTML = `<span class="file-icon">${getIcon(ext)}</span>${name}`;
      div.onclick = () => openFile(name, val, path + '/' + name);
      container.appendChild(div);
    } else {
      const fold  = document.createElement('div');
      fold.className = 'folder-node';
      fold.innerHTML = `<span class="folder-icon">▸</span>${name}/`;
      const inner = document.createElement('div');
      inner.className = 'folder-inner collapsed';
      buildTree(val, inner, path + '/' + name);
      fold.onclick = e => {
        e.stopPropagation();
        inner.classList.toggle('collapsed');
        fold.querySelector('.folder-icon').textContent =
          inner.classList.contains('collapsed') ? '▸' : '▾';
      };
      container.appendChild(fold);
      container.appendChild(inner);
    }
  }
}

function getIcon(ext) {
  const map = {
    txt:'📄', log:'📋', reg:'🔑', ps1:'⚡',
    py:'🐍',  sh:'💲',  pem:'🔒', conf:'⚙', csv:'📊',
  };
  return map[ext] || '📄';
}

// ── File viewer ────────────────────────────────────────────
function openFile(name, fileData, path) {
  STATE.openFile = fileData;
  STATE.viewMode = 'normal';
  el.viewerPath.textContent = '// ' + path.replace(/^\//, '');
  el.viewerPh.classList.add('hidden');
  el.viewerContent.classList.remove('hidden');
  el.viewerContent.textContent = fileData.content;

  if (fileData.clue && !STATE.cluesFound.has(path)) {
    STATE.cluesFound.add(path);
    addClue(fileData.clue, name);
    STATE.score += 50;
    el.hdrScore.textContent = STATE.score;
    updateClueCount();
    notify(`Clue discovered: [${fileData.clue.tag}]`, 'ok');
    apiFetch('/api/clue/', {
      sessionId: STATE.sessionId,
      missionId: STATE.level,
      cluesFound: STATE.cluesFound.size,
    });
  }
}

function resetViewer() {
  el.viewerPath.textContent = '// SELECT A FILE TO INSPECT';
  el.viewerPh.classList.remove('hidden');
  el.viewerContent.classList.add('hidden');
  el.viewerContent.textContent = '';
  STATE.openFile = null;
}

el.btnHex.addEventListener('click', () => {
  if (!STATE.openFile) return;
  if (STATE.viewMode === 'hex') {
    STATE.viewMode = 'normal';
    el.viewerContent.textContent = STATE.openFile.content;
    return;
  }
  STATE.viewMode = 'hex';
  const bytes = Array.from(STATE.openFile.content.slice(0, 256))
    .map(c => c.charCodeAt(0).toString(16).padStart(2, '0'));
  let out = '', i = 0;
  while (i < bytes.length) {
    const row = bytes.slice(i, i + 16);
    out += (i).toString(16).padStart(8, '0') + '  ' +
      row.join(' ').padEnd(47) + '  ' +
      row.map(h => {
        const n = parseInt(h, 16);
        return n >= 32 && n < 127 ? String.fromCharCode(n) : '.';
      }).join('') + '\n';
    i += 16;
  }
  el.viewerContent.textContent = out;
});

el.btnStrings.addEventListener('click', () => {
  if (!STATE.openFile) return;
  const strings = STATE.openFile.content.match(/[\x20-\x7e]{6,}/g) || ['No printable strings found.'];
  el.viewerContent.textContent = strings.join('\n');
});

el.btnMeta.addEventListener('click', () => {
  if (!STATE.openFile) return;
  el.viewerContent.textContent =
    `Size:  ${STATE.openFile.content.length} bytes\n` +
    `Lines: ${STATE.openFile.content.split('\n').length}\n` +
    `Type:  ${STATE.openFile.clue ? 'EVIDENCE [' + STATE.openFile.clue.tag + ']' : 'DATA'}`;
});

// ── System logs ────────────────────────────────────────────
function renderLogs(logs) {
  el.logPanel.innerHTML = '';
  logs.forEach(l => {
    const d = document.createElement('div');
    d.className = `log-entry log-${l.level.toLowerCase()}`;
    d.innerHTML =
      `<span class="log-time">${l.time}</span>` +
      `<span class="log-lvl">${l.level}</span>` +
      `<span class="log-msg">${l.msg}</span>`;
    el.logPanel.appendChild(d);
  });
  el.logBadge.textContent = `${logs.length} NEW`;
  setTimeout(() => { el.logBadge.textContent = `${logs.length}`; }, 3000);
}

// ── Clue board ─────────────────────────────────────────────
function addClue(clue, fname) {
  const card = document.createElement('div');
  card.className = 'clue-card new';
  card.innerHTML =
    `<span class="clue-tag tag-${clue.tag}">${clue.tag}</span>` +
    `<div class="clue-text">${clue.text}</div>` +
    `<div class="clue-file">${fname}</div>`;
  el.clueBoard.insertBefore(card, el.clueBoard.firstChild);
  setTimeout(() => card.classList.remove('new'), 2000);
}

function updateClueCount() {
  const total = currentMission ? currentMission.totalClues : 0;
  el.clueCount.textContent = `${STATE.cluesFound.size}/${total}`;
}

// ── Terminal ───────────────────────────────────────────────
el.termSubmit.addEventListener('click', execCmd);
el.termInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') { execCmd(); return; }
  if (e.key === 'ArrowUp') {
    if (cmdHistIdx < cmdHistory.length - 1)
      el.termInput.value = cmdHistory[++cmdHistIdx];
    e.preventDefault();
  }
  if (e.key === 'ArrowDown') {
    if (cmdHistIdx > 0) el.termInput.value = cmdHistory[--cmdHistIdx];
    else { cmdHistIdx = -1; el.termInput.value = ''; }
    e.preventDefault();
  }
});

// Block paste into terminal input too
el.termInput.addEventListener('paste', e => {
  e.preventDefault();
  registerViolation('Paste into terminal blocked', 'mid', PENALTIES.copyPaste);
});

el.answerInput.addEventListener('paste', e => {
  e.preventDefault();
  registerViolation('Paste into answer field blocked', 'mid', PENALTIES.copyPaste);
});

function execCmd() {
  const raw = el.termInput.value.trim();
  if (!raw) return;
  cmdHistory.unshift(raw);
  cmdHistIdx = -1;
  el.termInput.value = '';
  addTermLine('$ ' + raw, 'th-cmd');
  const parts = raw.split(/\s+/);
  const cmd   = parts[0].toLowerCase();
  const arg   = parts.slice(1).join(' ');

  if      (cmd === 'help')    showHelp();
  else if (cmd === 'ls')      addTermLine(listFiles(), 'th-out');
  else if (cmd === 'cat')     catFile(arg);
  else if (cmd === 'grep')    grepContent(arg);
  else if (cmd === 'decode')  decodeB64(arg);
  else if (cmd === 'xor')     xorDecode(arg);
  else if (cmd === 'clear')   el.termHistory.innerHTML = '';
  else if (cmd === 'whoami')  addTermLine(CFG.operativeName || 'GHOST', 'th-ok');
  else if (cmd === 'mission') addTermLine(`Mission ${STATE.level}: ${currentMission?.title}`, 'th-out');
  else if (cmd === 'score')   addTermLine(`Current score: ${STATE.score} pts`, 'th-ok');
  else if (cmd === 'time')    addTermLine(`Time remaining: ${formatTime(STATE.timeLeft)}`, 'th-out');
  else if (cmd === 'clues')   addTermLine(`Clues found: ${STATE.cluesFound.size}/${currentMission?.totalClues}`, 'th-out');
  else addTermLine(`Command not found: ${cmd}. Type 'help'`, 'th-err');
}

function showHelp() {
  const help =
    `Available commands:\n` +
    `  help           — show this help\n` +
    `  ls             — list all files in current mission\n` +
    `  cat <file>     — display file contents + collect clue\n` +
    `  grep <pattern> — search all files for pattern\n` +
    `  decode <b64>   — base64 decode a string\n` +
    `  xor <hex> <key>— XOR decode hex with single-byte key (e.g. xor 4b3f 0x4B)\n` +
    `  time           — show time remaining\n` +
    `  clues          — show clue progress\n` +
    `  whoami         — show operative name\n` +
    `  mission        — show current mission info\n` +
    `  score          — show current score\n` +
    `  clear          — clear terminal`;
  addTermLine(help, 'th-out');
}

function addTermLine(text, cls) {
  const d = document.createElement('div');
  d.className = `th-line ${cls}`;
  d.textContent = text;
  el.termHistory.appendChild(d);
  el.termHistory.scrollTop = el.termHistory.scrollHeight;
}

function listFiles() {
  const flat = (node, pre = '') => {
    let o = [];
    for (const [k, v] of Object.entries(node)) {
      if (v.content !== undefined) o.push(pre + k);
      else o.push(...flat(v, pre + k + '/'));
    }
    return o;
  };
  const files = flat(currentMission.fileSystem);
  return files.length ? files.join('\n') : 'No files found.';
}

function catFile(pat) {
  if (!pat) { addTermLine('Usage: cat <filename>', 'th-err'); return; }
  const result = findFile(pat, currentMission.fileSystem);
  if (result) {
    const { file, path } = result;
    const preview = file.content.slice(0, 400);
    addTermLine(preview + (file.content.length > 400 ? '\n...[truncated — open file to see full content]' : ''), 'th-out');
    if (file.clue && !STATE.cluesFound.has(path)) {
      STATE.cluesFound.add(path);
      addClue(file.clue, pat);
      STATE.score += 50;
      el.hdrScore.textContent = STATE.score;
      updateClueCount();
      notify(`Clue collected via terminal: [${file.clue.tag}]`, 'ok');
      apiFetch('/api/clue/', {
        sessionId: STATE.sessionId,
        missionId: STATE.level,
        cluesFound: STATE.cluesFound.size,
      });
    }
  } else {
    addTermLine(`cat: ${pat}: No such file`, 'th-err');
  }
}

function grepContent(pat) {
  if (!pat) { addTermLine('Usage: grep <pattern>', 'th-err'); return; }
  const flat = node => {
    let o = [];
    for (const [, v] of Object.entries(node)) {
      if (v.content !== undefined) o.push(v.content);
      else o.push(...flat(v));
    }
    return o;
  };
  const re      = new RegExp(pat, 'gi');
  const matches = flat(currentMission.fileSystem)
    .join('\n').split('\n')
    .filter(l => re.test(l));
  if (matches.length)
    addTermLine(matches.slice(0, 15).join('\n'), 'th-ok');
  else
    addTermLine(`grep: no matches for '${pat}'`, 'th-err');
}

function decodeB64(str) {
  if (!str) { addTermLine('Usage: decode <base64_string>', 'th-err'); return; }
  try {
    addTermLine('Decoded: ' + atob(str.trim()), 'th-ok');
  } catch {
    addTermLine('Error: invalid Base64 string', 'th-err');
  }
}

function xorDecode(args) {
  const parts = args.split(/\s+/);
  if (parts.length < 2) {
    addTermLine('Usage: xor <hex_string> <key_0xNN>  e.g. xor 2b4f1a 0x4B', 'th-err');
    return;
  }
  try {
    const hexStr = parts[0];
    const key    = parseInt(parts[1], 16);
    const bytes  = hexStr.match(/.{1,2}/g) || [];
    const result = bytes.map(h => String.fromCharCode(parseInt(h, 16) ^ key)).join('');
    addTermLine('XOR decoded: ' + result, 'th-ok');
  } catch {
    addTermLine('XOR error: invalid input', 'th-err');
  }
}

function findFile(name, node, path = '') {
  for (const [k, v] of Object.entries(node)) {
    const cur = path + '/' + k;
    if (k === name && v.content !== undefined) return { file: v, path: cur };
    if (typeof v === 'object' && v.content === undefined) {
      const r = findFile(name, v, cur);
      if (r) return r;
    }
  }
  return null;
}

// ── Answer submit ──────────────────────────────────────────
el.answerSubmit.addEventListener('click', submitAnswer);
el.answerInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') submitAnswer();
});

async function submitAnswer() {
  const val = el.answerInput.value.trim().toLowerCase();
  if (!val) return;

  const res = await apiFetch('/api/submit/', {
    missionId:     STATE.level,
    answer:        val,
    timeLeft:      STATE.timeLeft,
    cluesFound:    STATE.cluesFound.size,
    wrongAttempts: STATE.wrongAttempts,
    currentScore:  STATE.score,
    sessionId:     STATE.sessionId,
  });

  if (res.correct) {
    const earned = res.earned;
    STATE.score += earned;
    el.hdrScore.textContent  = STATE.score;
    el.answerFeedback.textContent = '✔ CORRECT — TRACE VERIFIED';
    el.answerFeedback.className   = 'fb-correct';
    clearInterval(STATE.timerInterval);
    monitorLog(`Mission ${STATE.level} solved. +${earned} pts`, 'low');
    setTimeout(() => {
      el.modalBody.innerHTML =
        `<strong>Level ${STATE.level} complete!</strong><br><br>` +
        `Time bonus:       +${STATE.timeLeft * 2}<br>` +
        `Clues found:      +${STATE.cluesFound.size * 25}<br>` +
        `Wrong penalties:  -${STATE.wrongAttempts * 30}<br>` +
        `<br><strong>Earned: +${earned} pts</strong><br>` +
        `Total score: <strong style="color:var(--green)">${STATE.score}</strong>`;
      el.modalOverlay.classList.remove('hidden');
    }, 600);
  } else {
    STATE.wrongAttempts++;
    STATE.score = Math.max(0, STATE.score - 30);
    el.hdrScore.textContent       = STATE.score;
    el.answerFeedback.textContent = `✘ INCORRECT (-30 pts) — Attempt ${STATE.wrongAttempts}`;
    el.answerFeedback.className   = 'fb-wrong';
    notify('Wrong answer — keep digging', 'warn');
    if (STATE.wrongAttempts >= 5) {
      clearInterval(STATE.timerInterval);
      await endSession('failed');
      showGameOver('Too many wrong attempts — connection severed.');
    }
  }
}

// ── Hint ───────────────────────────────────────────────────
el.hintBtn.addEventListener('click', async () => {
  if (STATE.hintUsed) return;
  STATE.hintUsed = true;
  const res = await apiFetch('/api/hint/', {
    missionId: STATE.level,
    sessionId: STATE.sessionId,
  });
  STATE.score = Math.max(0, STATE.score - res.cost);
  el.hdrScore.textContent  = STATE.score;
  el.hintText.textContent  = '▸ ' + res.hint;
  el.hintBtn.disabled      = true;
  el.hintBtn.innerHTML     = 'INTEL USED';
  notify(`Intel requested: -${res.cost} pts`, 'warn');
});

// ── Timer ──────────────────────────────────────────────────
function startTimer(seconds) {
  clearInterval(STATE.timerInterval);
  STATE.timeLeft = seconds;
  updateTimerDisplay();
  STATE.timerInterval = setInterval(async () => {
    if (CHEAT.locked) return;
    STATE.timeLeft--;
    updateTimerDisplay();
    if (STATE.timeLeft <= 30) {
      el.hdrTimer.style.color     = 'var(--red)';
      el.hdrTimer.style.animation = 'blink .5s infinite';
    }
    if (STATE.timeLeft <= 0) {
      clearInterval(STATE.timerInterval);
      await endSession('failed');
      showGameOver('Time limit exceeded — uplink terminated.');
    }
  }, 1000);
}

function updateTimerDisplay() {
  el.hdrTimer.textContent = formatTime(STATE.timeLeft);
}

function formatTime(s) {
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
}

// ── Modals ─────────────────────────────────────────────────
el.modalNext.addEventListener('click', () => {
  el.modalOverlay.classList.add('hidden');
  loadLevel(STATE.level);   // STATE.level already incremented by API
});

el.goRestart.addEventListener('click', async () => {
  el.gameoverOverlay.classList.add('hidden');
  STATE.score          = 0;
  STATE.wrongAttempts  = 0;
  CHEAT.violations     = 0;
  CHEAT.focusBreaks    = 0;
  CHEAT.tabSwitches    = 0;
  CHEAT.rightClicks    = 0;
  el.hdrTimer.style.color     = '';
  el.hdrTimer.style.animation = '';
  el.monitorLog.innerHTML     = '';
  updateMonitorStats();
  const r = await apiFetch('/api/session/start/', {});
  STATE.sessionId    = r.sessionId;
  STATE.sessionStart = Date.now();
  loadLevel(0);
});

async function endSession(status) {
  if (!STATE.sessionId) return;
  const timeTaken = Math.floor((Date.now() - STATE.sessionStart) / 1000);
  await apiFetch('/api/session/end/', {
    sessionId:         STATE.sessionId,
    finalScore:        STATE.score,
    missionsCompleted: STATE.level - 1,
    violations:        CHEAT.violations,
    timeTaken,
    status,
  });
}

function showGameOver(reason) {
  el.goBody.innerHTML =
    `${reason}<br><br>` +
    `Final score: <strong style="color:var(--yellow)">${STATE.score}</strong><br>` +
    `Violations:  <strong style="color:var(--red)">${CHEAT.violations}</strong>`;
  el.gameoverOverlay.classList.remove('hidden');
}

async function showVictory() {
  clearInterval(STATE.timerInterval);
  el.goBody.innerHTML =
    `<span style="color:var(--green)">OPERATION LACUNA — NEUTRALISED</span><br>` +
    `<span style="color:var(--cyan)">40 MILLION PEOPLE NEVER LOSE POWER.</span><br><br>` +
    `LACE is in custody. PHANTOM CIRCUIT dismantled.<br><br>` +
    `Final score: <strong style="color:var(--yellow)">${STATE.score}</strong><br>` +
    `Violations: ${CHEAT.violations}<br><br>` +
    `<span style="color:var(--green)">🏆 SOVEREIGN ANALYST</span>`;
  $('go-icon').textContent  = '★';
  $('go-icon').style.color  = 'var(--yellow)';
  $('go-title').textContent = 'SOVEREIGN ANALYST';
  $('go-title').style.color = 'var(--green)';
  $('go-restart').textContent = 'PLAY AGAIN';
  el.gameoverOverlay.classList.remove('hidden');
}

// ── Notification toast ─────────────────────────────────────
let notifTimer;
function notify(msg, type = 'info') {
  clearTimeout(notifTimer);
  el.notif.textContent = '▸ ' + msg;
  el.notif.className   = `notif-${type}`;
  el.notif.classList.remove('hidden');
  notifTimer = setTimeout(() => el.notif.classList.add('hidden'), 3200);
}

// ══════════════════════════════════════════════════════════
// ── ANTI-CHEAT / INTEGRITY MONITOR ────────────────────────
// ══════════════════════════════════════════════════════════

function monitorLog(msg, severity = 'low') {
  const now = new Date();
  const ts  = [now.getHours(), now.getMinutes(), now.getSeconds()]
    .map(n => String(n).padStart(2, '0')).join(':');
  const icons = { low: 'ℹ', mid: '⚠', high: '⛔' };
  const entry = document.createElement('div');
  entry.className = `mlog-entry sev-${severity}`;
  entry.innerHTML =
    `<span class="mlog-time">${ts}</span>` +
    `<span class="mlog-icon">${icons[severity]}</span>` +
    `<span class="mlog-msg">${msg}</span>`;
  el.monitorLog.appendChild(entry);
  el.monitorLog.scrollTop = el.monitorLog.scrollHeight;
}

function updateMonitorStats() {
  const integrity = Math.max(0, 100 - CHEAT.violations * 8 - CHEAT.focusBreaks * 3);
  el.statIntegrity.textContent   = integrity + '%';
  el.statViolations.textContent  = CHEAT.violations;
  el.statFocus.textContent       = CHEAT.focusBreaks;
  el.statDevtools.textContent    = CHEAT.devToolsOpen ? 'OPEN!' : 'CLEAR';
  el.statTabs.textContent        = CHEAT.tabSwitches;
  el.statRightclicks.textContent = CHEAT.rightClicks;
  if (CHEAT.violations > 0 || CHEAT.devToolsOpen)
    el.monitorToggle.classList.add('alert');
}

function registerViolation(msg, severity, penalty) {
  if (el.game.classList.contains('hidden')) return;
  CHEAT.violations++;
  STATE.score = Math.max(0, STATE.score - penalty);
  el.hdrScore.textContent = STATE.score;
  monitorLog(`VIOLATION #${CHEAT.violations}: ${msg} | -${penalty} pts`, severity);
  updateMonitorStats();
  notify(`⚠ BLOCKED: ${msg}`, 'err');
  apiFetch('/api/violation/', {
    sessionId: STATE.sessionId,
    eventType: msg,
    penalty,
    severity,
  });
  if (CHEAT.violations >= 5)
    triggerLockout(`REPEATED VIOLATIONS (${CHEAT.violations}×) — terminal locked.`, 12);
}

function triggerLockout(reason, duration = 8) {
  if (CHEAT.locked) return;
  CHEAT.locked = true;
  clearInterval(STATE.timerInterval);
  el.lockoutMsg.innerHTML =
    `<strong style="color:var(--red)">${reason}</strong><br><br>` +
    `Integrity breach logged to NEXUS. Score penalty applied.`;
  el.lockoutResume.style.display = 'none';
  el.lockoutOverlay.classList.remove('hidden');
  let t = duration;
  el.lockoutCountdown.textContent = t + 's';
  CHEAT.lockTimer = setInterval(() => {
    t--;
    el.lockoutCountdown.textContent = t + 's';
    if (t <= 0) {
      clearInterval(CHEAT.lockTimer);
      el.lockoutCountdown.textContent = '';
      el.lockoutResume.style.display  = 'inline-block';
    }
  }, 1000);
}

el.lockoutResume && (el.lockoutResume.onclick = () => {
  CHEAT.locked = false;
  el.lockoutOverlay.classList.add('hidden');
  startTimer(STATE.timeLeft);
});

// ── Block: right-click ─────────────────────────────────────
document.addEventListener('contextmenu', e => {
  e.preventDefault();
  CHEAT.rightClicks++;
  updateMonitorStats();
  monitorLog(`Right-click blocked #${CHEAT.rightClicks}`, 'low');
  return false;
});

// ── Block: copy / cut / paste (ALL methods) ────────────────
document.addEventListener('copy', e => {
  e.preventDefault();
  if (!el.game.classList.contains('hidden'))
    registerViolation('Copy attempt blocked', 'mid', PENALTIES.copyPaste);
});

document.addEventListener('cut', e => {
  e.preventDefault();
  if (!el.game.classList.contains('hidden'))
    registerViolation('Cut attempt blocked', 'mid', PENALTIES.copyPaste);
});

document.addEventListener('paste', e => {
  e.preventDefault();
  if (!el.game.classList.contains('hidden'))
    registerViolation('Paste attempt blocked', 'mid', PENALTIES.copyPaste);
});

// ── Block: keyboard shortcuts ──────────────────────────────
document.addEventListener('keydown', e => {
  const ctrl   = e.ctrlKey || e.metaKey;
  const key    = e.key.toLowerCase();
  const active = document.activeElement;
  const isInput = active.tagName === 'INPUT' || active.tagName === 'TEXTAREA';

  // View source
  if ((ctrl && key === 'u') || e.key === 'F12') {
    e.preventDefault();
    registerViolation('View source / DevTools blocked', 'high', PENALTIES.viewSource);
    return false;
  }
  // Print
  if (ctrl && key === 'p') {
    e.preventDefault();
    registerViolation('Print blocked', 'low', PENALTIES.printScreen);
    return false;
  }
  // Save page
  if (ctrl && key === 's') {
    e.preventDefault();
    registerViolation('Save page blocked', 'low', 25);
    return false;
  }
  // Find
  if (ctrl && key === 'f') {
    e.preventDefault();
    monitorLog('Ctrl+F blocked.', 'low');
    return false;
  }
  // Copy — blocked everywhere
  if (ctrl && key === 'c') {
    e.preventDefault();
    registerViolation('Copy (Ctrl+C) blocked', 'mid', PENALTIES.copyPaste);
    return false;
  }
  // Cut — blocked everywhere
  if (ctrl && key === 'x') {
    e.preventDefault();
    registerViolation('Cut (Ctrl+X) blocked', 'mid', PENALTIES.copyPaste);
    return false;
  }
  // Paste — blocked everywhere including inputs
  if (ctrl && key === 'v') {
    e.preventDefault();
    registerViolation('Paste (Ctrl+V) blocked', 'mid', PENALTIES.copyPaste);
    return false;
  }
  // Select all — blocked outside inputs
  if (ctrl && key === 'a' && !isInput) {
    e.preventDefault();
    return false;
  }
});

// ── Block: drag & drop ─────────────────────────────────────
document.addEventListener('dragstart', e => e.preventDefault());
document.addEventListener('drop', e => {
  e.preventDefault();
  if (!el.game.classList.contains('hidden'))
    registerViolation('Drag & drop blocked', 'mid', PENALTIES.copyPaste);
});
document.addEventListener('dragover', e => e.preventDefault());

// ── Block: text selection outside inputs ───────────────────
document.addEventListener('selectstart', e => {
  const t = e.target;
  if (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA') return;
  e.preventDefault();
});

// ── Tab / window focus ─────────────────────────────────────
document.addEventListener('visibilitychange', () => {
  if (el.game.classList.contains('hidden')) return;
  if (document.hidden) {
    CHEAT.tabSwitches++;
    CHEAT.focusBreaks++;
    STATE.score = Math.max(0, STATE.score - PENALTIES.focusBreak);
    el.hdrScore.textContent = STATE.score;
    monitorLog(`Tab hidden #${CHEAT.tabSwitches} | -${PENALTIES.focusBreak} pts`, 'mid');
    updateMonitorStats();
  } else {
    showSuspiciousWarning('TAB SWITCH', `#${CHEAT.tabSwitches}`);
  }
});

window.addEventListener('blur', () => {
  if (el.game.classList.contains('hidden') || document.hidden) return;
  CHEAT.focusBreaks++;
  STATE.score = Math.max(0, STATE.score - PENALTIES.focusBreak);
  el.hdrScore.textContent = STATE.score;
  monitorLog(`Window focus lost #${CHEAT.focusBreaks} | -${PENALTIES.focusBreak} pts`, 'mid');
  updateMonitorStats();
});

window.addEventListener('focus', () => {
  if (el.game.classList.contains('hidden') || document.hidden) return;
  if (CHEAT.focusBreaks > 0)
    showSuspiciousWarning('WINDOW FOCUS LOST', `#${CHEAT.focusBreaks}`);
});

// ── Suspicious activity warning overlay ────────────────────
function showSuspiciousWarning(eventType, occurrence) {
  if (!warnEl.overlay) return;
  const now = new Date();
  const ts  = [now.getHours(), now.getMinutes(), now.getSeconds()]
    .map(n => String(n).padStart(2, '0')).join(':');
  warnEl.eventType.textContent  = eventType;
  warnEl.timestamp.textContent  = ts;
  warnEl.occurrence.textContent = occurrence;
  warnEl.penalty.textContent    = `-${PENALTIES.focusBreak} PTS`;
  warnEl.overlay.classList.remove('hidden');

  clearInterval(STATE.timerInterval);
  STATE.timerInterval = null;

  let secs = 5;
  warnEl.seconds.textContent  = secs;
  warnEl.bar.style.transition = 'none';
  warnEl.bar.style.transform  = 'scaleX(1)';
  void warnEl.bar.offsetWidth;
  warnEl.bar.style.transition = `transform ${secs}s linear`;
  warnEl.bar.style.transform  = 'scaleX(0)';

  clearInterval(warnCountdownTimer);
  clearTimeout(warnAutoClose);
  warnCountdownTimer = setInterval(() => {
    secs--;
    warnEl.seconds.textContent = secs;
    if (secs <= 0) { clearInterval(warnCountdownTimer); dismissWarning(); }
  }, 1000);
  warnAutoClose = setTimeout(dismissWarning, 6000);
}

function dismissWarning() {
  clearInterval(warnCountdownTimer);
  clearTimeout(warnAutoClose);
  if (!warnEl.overlay) return;
  warnEl.overlay.classList.add('hidden');
  if (!CHEAT.locked && STATE.timeLeft > 0) startTimer(STATE.timeLeft);
}

warnEl.dismiss && warnEl.dismiss.addEventListener('click', dismissWarning);

document.addEventListener('keydown', e => {
  if (!warnEl.overlay || warnEl.overlay.classList.contains('hidden')) return;
  if (e.key === 'Enter' || e.key === 'Escape' || e.key === ' ') {
    e.preventDefault();
    dismissWarning();
  }
});

// ── DevTools detection ─────────────────────────────────────
setInterval(() => {
  const wDiff     = window.outerWidth  - window.innerWidth;
  const hDiff     = window.outerHeight - window.innerHeight;
  const suspected = wDiff > 160 || hDiff > 160;
  if (suspected && !CHEAT.devToolsOpen) {
    CHEAT.devToolsOpen = true;
    if (!el.game.classList.contains('hidden')) {
      triggerLockout('DEVELOPER TOOLS DETECTED — terminal locked.', 15);
      registerViolation('DevTools opened', 'high', PENALTIES.devtools);
    }
  } else if (!suspected && CHEAT.devToolsOpen) {
    CHEAT.devToolsOpen = false;
    monitorLog('DevTools closed.', 'low');
    updateMonitorStats();
  }
}, 1500);

// ── Monitor panel toggle ───────────────────────────────────
el.monitorToggle.addEventListener('click', () => {
  CHEAT.monitorVisible = !CHEAT.monitorVisible;
  el.monitorPanel.classList.toggle('hidden', !CHEAT.monitorVisible);
  el.monitorToggle.textContent =
    CHEAT.monitorVisible ? '📡 HIDE MONITOR' : '📡 MONITOR';
  if (CHEAT.monitorVisible) el.monitorToggle.classList.remove('alert');
});

el.monitorClose.addEventListener('click', () => {
  CHEAT.monitorVisible = false;
  el.monitorPanel.classList.add('hidden');
  el.monitorToggle.textContent = '📡 MONITOR';
});

// ── Init ───────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', boot);