const healthChip = document.getElementById('healthChip');
const rocAucEl = document.getElementById('rocAuc');
const avgPrecisionEl = document.getElementById('avgPrecision');
const totalChecksEl = document.getElementById('totalChecks');
const highChecksEl = document.getElementById('highChecks');
const mediumChecksEl = document.getElementById('mediumChecks');
const lowChecksEl = document.getElementById('lowChecks');
const feedList = document.getElementById('feedList');

const transactionForm = document.getElementById('transactionForm');
const urlForm = document.getElementById('urlForm');
const fileForm = document.getElementById('fileForm');
const quickPhishingBtn = document.getElementById('quickPhishing');
const quickFileBtn = document.getElementById('quickFile');
const quickTxBtn = document.getElementById('quickTx');

const tabs = document.querySelectorAll('.tab');
const panes = document.querySelectorAll('.tab-pane');

const state = {
  total: 0,
  HIGH: 0,
  MEDIUM: 0,
  LOW: 0,
};

function riskClass(level) {
  return level === 'HIGH' ? 'risk-high' : level === 'MEDIUM' ? 'risk-medium' : 'risk-low';
}

function updateKpis(level) {
  state.total += 1;
  state[level] += 1;
  totalChecksEl.textContent = String(state.total);
  highChecksEl.textContent = String(state.HIGH);
  mediumChecksEl.textContent = String(state.MEDIUM);
  lowChecksEl.textContent = String(state.LOW);
}

function createPost({ type, title, probability, level, reasons }) {
  const post = document.createElement('article');
  post.className = 'post';

  const reasonItems = (reasons || []).map((reason) => `<li>${reason}</li>`).join('');
  const now = new Date().toLocaleTimeString();

  post.innerHTML = `
    <div class="post-head">
      <div>
        <div class="post-type">${type}</div>
        <strong>${title}</strong>
      </div>
      <span class="risk-badge ${riskClass(level)}">${level}</span>
    </div>
    <div class="prob">${(probability * 100).toFixed(2)}%</div>
    <ul class="reason-list">${reasonItems}</ul>
    <div class="post-type">Posted at ${now}</div>
  `;

  feedList.prepend(post);
}

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((item) => item.classList.remove('active'));
    panes.forEach((pane) => pane.classList.remove('active'));
    tab.classList.add('active');
    document.querySelector(`[data-pane="${tab.dataset.tab}"]`).classList.add('active');
  });
});

function activateTab(tabName) {
  tabs.forEach((item) => item.classList.remove('active'));
  panes.forEach((pane) => pane.classList.remove('active'));
  document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
  document.querySelector(`[data-pane="${tabName}"]`).classList.add('active');
}

quickPhishingBtn.addEventListener('click', () => {
  activateTab('url');
  document.getElementById('urlInput').value = 'http://paypaI-security-check-login.example.com/verify/account';
});

quickFileBtn.addEventListener('click', () => {
  activateTab('file');
});

quickTxBtn.addEventListener('click', () => {
  activateTab('tx');
  document.getElementById('amount').value = '480.90';
  document.getElementById('channel').value = 'web';
  document.getElementById('cardPresent').value = '0';
  document.getElementById('hour').value = '1';
});

async function loadHealth() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    healthChip.textContent = data.status === 'ok' ? 'System Online' : 'System Offline';
  } catch {
    healthChip.textContent = 'System Offline';
  }
}

async function loadMetrics() {
  try {
    const res = await fetch('/metrics');
    if (!res.ok) throw new Error('metrics unavailable');
    const data = await res.json();
    rocAucEl.textContent = Number(data.roc_auc ?? 0).toFixed(3);
    avgPrecisionEl.textContent = Number(data.average_precision ?? 0).toFixed(3);
  } catch {
    rocAucEl.textContent = 'N/A';
    avgPrecisionEl.textContent = 'N/A';
  }
}

transactionForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    amount: Number(document.getElementById('amount').value),
    channel: document.getElementById('channel').value,
    card_present: Number(document.getElementById('cardPresent').value),
    hour: Number(document.getElementById('hour').value),
  };

  const res = await fetch('/score', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert(err.detail || 'Transaction scoring failed.');
    return;
  }

  const data = await res.json();
  createPost({
    type: 'Transaction Check',
    title: `${payload.channel.toUpperCase()} | £${payload.amount.toFixed(2)} | Hour ${payload.hour}`,
    probability: data.fraud_probability,
    level: data.risk_level,
    reasons: data.reasons,
  });
  updateKpis(data.risk_level);
});

urlForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const url = document.getElementById('urlInput').value.trim();

  const res = await fetch('/check/url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert(err.detail || 'URL check failed.');
    return;
  }

  const data = await res.json();
  createPost({
    type: 'Website URL Check',
    title: url,
    probability: data.fraud_probability,
    level: data.risk_level,
    reasons: data.reasons,
  });
  updateKpis(data.risk_level);
});

fileForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const fileInput = document.getElementById('fileInput');
  if (!fileInput.files || fileInput.files.length === 0) {
    alert('Please select a file.');
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch('/check/file', {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert(err.detail || 'File check failed.');
    return;
  }

  const data = await res.json();
  createPost({
    type: 'File Check',
    title: `${file.name} (${Math.round(file.size / 1024)} KB)`,
    probability: data.fraud_probability,
    level: data.risk_level,
    reasons: data.reasons,
  });
  updateKpis(data.risk_level);
  fileInput.value = '';
});

createPost({
  type: 'System Post',
  title: 'Welcome to FraudFeed',
  probability: 0.0,
  level: 'LOW',
  reasons: ['Run a transaction, URL, or file check to start the feed.'],
});

loadHealth();
loadMetrics();
