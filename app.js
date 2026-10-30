
// =====================================================================
// HYBRID ARCHITECTURE DETECTOR (NODE.JS SERVER vs GITHUB PAGES STANDALONE)
// =====================================================================
const IS_STANDALONE = window.location.hostname.includes('github.io') || 
                      window.location.protocol === 'file:' || 
                      (!window.location.port && !window.location.hostname.includes('localhost'));

console.log(`[ENGINE] Mode: ${IS_STANDALONE ? 'STANDALONE BROWSER CLIENT (GitHub Pages)' : 'FULL-STACK HYBRID (Node.js Active)'}`);

/**
 * Elaya Narayanan — Discussion Intelligence & AudioCRM Engine — Client Controller
 * Complete Non-Blocking Parallel Calling & Dynamic Auto-Schema Engine
 */

// Application State
let dataset = {
  fileName: '',
  baseColumns: [],
  insightColumns: [],
  rows: []
};

let queueStats = {
  activeWorkers: 0,
  queueLength: 0,
  maxConcurrency: 3,
  completedCount: 0
};

// Row-Level Audio Recording Engine (Web Audio API)
let activeRecording = {
  rowId: null,
  stream: null,
  mediaRecorder: null,
  audioContext: null,
  analyserNode: null,
  dataArray: null,
  chunks: [],
  startTime: 0,
  timerInterval: null,
  animFrameId: null,
  isPaused: false,
  pauseStartTime: 0,
  totalPausedDuration: 0
};

let selectedRowForDrawer = null;
let eventSource = null;

// =====================================================================
// INITIALIZATION
// =====================================================================
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  fetchInitialDataset();
  fetchMeetings();
  initSSE();
  setupDragAndDrop();
  setupSearch();
  setupRowAudioInput();
  initPortalMode();
});

// Fetch current dataset from server
async function fetchInitialDataset() {
  // Check local storage first
  const cached = localStorage.getItem('elaya_audiocrm_dataset');
  if (cached) {
    try {
      const parsed = JSON.parse(cached);
      if (parsed && parsed.rows && parsed.rows.length > 0) {
        dataset = parsed;
        updateStatsUI();
        renderGrid();
        if (IS_STANDALONE) return;
      }
    } catch (e) {}
  }

  try {
    const endpoint = IS_STANDALONE ? './data/current_dataset.json' : '/api/dataset';
    const res = await fetch(endpoint);
    const data = await res.json();
    const ds = data.dataset || data;
    if (ds && ds.rows) {
      dataset = ds;
      if (data.queue) queueStats = data.queue;
      updateStatsUI();
      renderGrid();
      return;
    }
  } catch (err) {
    console.warn('API fetch unavailable, trying static JSON fallback:', err);
  }

  // Fallback try static relative path
  try {
    const res2 = await fetch('data/current_dataset.json');
    const ds2 = await res2.json();
    if (ds2 && ds2.rows) {
      dataset = ds2;
      updateStatsUI();
      renderGrid();
    }
  } catch (e) {
    console.error('Initial dataset could not be loaded:', e);
  }
}

// =====================================================================
// SERVER-SENT EVENTS (SSE) — REAL-TIME EVENT STREAM
// =====================================================================
function initSSE() {
  if (IS_STANDALONE) {
    console.log('[SSE] Standalone mode: Real-time browser worker active.');
    return;
  }
  if (eventSource) eventSource.close();

  eventSource = new EventSource('/api/events');

  eventSource.onopen = () => {
    console.log('[SSE] Live stream connected.');
  };

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleLiveEvent(data);
    } catch (e) {
      console.warn('[SSE] Could not parse event:', event.data);
    }
  };

  eventSource.onerror = (err) => {
    console.warn('[SSE] Connection lost, reconnecting in 3s...');
    setTimeout(initSSE, 3000);
  };
}

function handleLiveEvent(data) {
  if (data.stats) {
    queueStats = data.stats;
    updateStatsUI();
  }

  switch (data.type) {
    case 'queue_update':
      updateRowStatusInGrid(data.rowId, 'queued', 'In AI Queue');
      break;

    case 'job_progress':
      const stageText = data.stage === 'transcribing' ? 'Transcribing Audio...' : 'Gemini Synthesizing...';
      updateRowStatusInGrid(data.rowId, data.stage, stageText);
      break;

    case 'row_completed':
      if (data.updatedRow) {
        const index = dataset.rows.findIndex(r => r._id === data.rowId);
        if (index !== -1) {
          dataset.rows[index] = data.updatedRow;
        }
        updateCompletedRowInGrid(data.updatedRow);
        updateStatsUI();
      }
      break;

    case 'row_failed':
      updateRowStatusInGrid(data.rowId, 'error', 'Processing Issue');
      break;

    case 'cell_overridden':
      const r = dataset.rows.find(row => row._id === data.rowId);
      if (r) {
        r[data.column] = data.newValue;
        if (!r._overriddenFields) r._overriddenFields = {};
        r._overriddenFields[data.column] = data.overriddenMeta;
        renderGrid();
      }
      break;

    case 'dataset_updated':
    case 'schema_updated':
      fetchInitialDataset();
      break;

    case 'meeting_segment_processed':
      if (activeMeetingSession && activeMeetingSession.id === data.meetingId) {
        appendSegmentToLiveTranscript(data.segment);
      }
      fetchMeetings();
      break;

    case 'meeting_finalized':
      fetchMeetings();
      if (selectedMeetingForModal && selectedMeetingForModal.id === data.meetingId) {
        openMeetingDetails(data.meetingId);
      }
      break;
  }
}

// Update Header Stats
function updateStatsUI() {
  document.getElementById('stat-sheet-name').innerText = dataset.fileName || 'No Sheet Loaded';
  document.getElementById('stat-total-rows').innerText = dataset.rows.length;
  
  const completedCount = dataset.rows.filter(r => r._status === 'completed').length;
  document.getElementById('stat-completed-rows').innerText = completedCount;

  // Queue Status
  const queueStatusEl = document.getElementById('stat-queue-status');
  const queuePulse = document.getElementById('queue-pulse');
  const queueLenEl = document.getElementById('stat-queue-len');

  if (queueStats.activeWorkers > 0) {
    queueStatusEl.innerHTML = `<span class="text-indigo-400 font-bold">${queueStats.activeWorkers} Active</span> <span class="text-slate-500">|</span> <span class="text-amber-400">${queueStats.queueLength} Queued</span>`;
    queuePulse.classList.remove('hidden');
  } else {
    queueStatusEl.innerHTML = `<span class="text-slate-400">Idle (Ready)</span> <span class="text-slate-500">|</span> <span>${queueStats.queueLength} Queued</span>`;
    queuePulse.classList.add('hidden');
  }

  // Calculate Average Confidence
  const scoredRows = dataset.rows.filter(r => r._confidence > 0);
  if (scoredRows.length > 0) {
    const avg = (scoredRows.reduce((acc, r) => acc + r._confidence, 0) / scoredRows.length).toFixed(1);
    document.getElementById('stat-confidence').innerText = `${avg}% Avg`;
  }
}

// =====================================================================
// DYNAMIC SPREADSHEET GRID RENDERER
// =====================================================================
function renderGrid() {
  const tableHead = document.getElementById('table-head');
  const tableBody = document.getElementById('table-body');
  const emptyState = document.getElementById('empty-state');

  if (!dataset.rows || dataset.rows.length === 0) {
    tableHead.innerHTML = '';
    tableBody.innerHTML = '';
    emptyState.classList.remove('hidden');
    return;
  }
  emptyState.classList.add('hidden');

  // Filter rows based on search and status
  const searchTerm = (document.getElementById('grid-search')?.value || '').toLowerCase();
  const statusFilter = document.getElementById('status-filter')?.value || 'all';

  const filteredRows = dataset.rows.filter(row => {
    // Status filter
    if (statusFilter === 'completed' && row._status !== 'completed') return false;
    if (statusFilter === 'queued' && (row._status === 'idle' || row._status === 'completed')) return false;
    if (statusFilter === 'idle' && row._status !== 'idle') return false;

    // Search term
    if (!searchTerm) return true;
    for (const key of [...dataset.baseColumns, ...dataset.insightColumns]) {
      if (String(row[key] || '').toLowerCase().includes(searchTerm)) return true;
    }
    if ((row._transcript || '').toLowerCase().includes(searchTerm)) return true;
    return false;
  });

  // 1. Build Header
  let headHtml = `
    <!-- Top Header Grouping Row -->
    <tr class="text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
      <th class="sticky-col px-4 py-2 bg-[#090d16] border-r border-slate-800 text-sky-400 font-bold min-w-[240px]">
        🎙️ Call Session Controls
      </th>
      <th colspan="${dataset.baseColumns.length}" class="px-4 py-1.5 bg-slate-900/60 border-r border-slate-800 font-bold text-slate-300">
        <div class="flex items-center gap-1.5">
          <i data-lucide="database" class="w-3.5 h-3.5 text-slate-400"></i>
          Base Information (Customer Context)
        </div>
      </th>
      <th colspan="${dataset.insightColumns.length}" class="px-4 py-1.5 bg-teal-950/20 border-r border-slate-800 font-bold text-teal-400">
        <div class="flex items-center gap-1.5">
          <i data-lucide="sparkles" class="w-3.5 h-3.5 text-teal-400"></i>
          Insight Fields (Dynamic AI Extracted)
        </div>
      </th>
      <th colspan="2" class="px-4 py-1.5 bg-indigo-950/20 font-bold text-indigo-300">
        <div class="flex items-center gap-1.5">
          <i data-lucide="shield-check" class="w-3.5 h-3.5 text-indigo-400"></i>
          Master Audit & Verification
        </div>
      </th>
    </tr>

    <!-- Exact Column Headers Row -->
    <tr class="text-[11px] font-semibold text-slate-300 bg-[#0d1424]">
      <th class="sticky-col px-4 py-3 bg-[#0d1424] border-r border-slate-800 text-slate-400">
        Session Status & Actions
      </th>
  `;

  // Base Columns
  dataset.baseColumns.forEach(col => {
    headHtml += `
      <th class="px-4 py-3 whitespace-nowrap border-r border-slate-800/80 text-slate-300 font-mono text-[11px] bg-slate-900/30">
        ${escapeHtml(col)}
      </th>
    `;
  });

  // Insight Columns
  dataset.insightColumns.forEach(col => {
    headHtml += `
      <th class="px-4 py-3 min-w-[260px] max-w-[340px] border-r border-slate-800/80 text-teal-300 font-semibold bg-teal-950/10">
        <div class="flex items-center justify-between gap-2">
          <span>${escapeHtml(col)}</span>
          <span class="text-[9px] px-1.5 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">AI</span>
        </div>
      </th>
    `;
  });

  // Audit Columns
  headHtml += `
      <th class="px-4 py-3 whitespace-nowrap border-r border-slate-800/80 text-indigo-300">Sentiment & Score</th>
      <th class="px-4 py-3 whitespace-nowrap text-slate-300 text-center">Master Transcript</th>
    </tr>
  `;
  tableHead.innerHTML = headHtml;

  // 2. Build Body Rows
  let bodyHtml = '';
  filteredRows.forEach(row => {
    const isThisRecording = activeRecording.rowId === row._id;
    const isCompleted = row._status === 'completed';
    const isProcessing = ['queued', 'transcribing', 'synthesizing'].includes(row._status);

    bodyHtml += `
      <tr id="row-${row._id}" class="hover:bg-slate-800/40 transition group/row">
        <!-- Sticky Session Controls Cell -->
        <td class="sticky-col px-3 py-3 border-r border-slate-800 align-middle">
          <div id="session-cell-${row._id}" class="flex items-center gap-2">
            ${renderSessionCellContent(row)}
          </div>
        </td>
    `;

    // Base Information Columns (Read-only context)
    dataset.baseColumns.forEach(col => {
      const val = row[col] || '—';
      bodyHtml += `
        <td class="px-4 py-3 whitespace-nowrap border-r border-slate-800/60 font-mono text-slate-300">
          ${escapeHtml(val)}
        </td>
      `;
    });

    // Insight Fields (AI Extracted, Double-Click to Override)
    dataset.insightColumns.forEach(col => {
      const val = row[col] || '';
      const isOverridden = row._overriddenFields && row._overriddenFields[col];
      const hasContent = val.trim() !== '';

      bodyHtml += `
        <td class="px-4 py-3 border-r border-slate-800/60 editable-cell align-top text-slate-200"
            ondblclick="startCellEdit('${row._id}', '${escapeAttr(col)}', this)"
            title="${isOverridden ? `Original AI: ${escapeAttr(isOverridden.originalValue)}` : 'Double click to override'}">
          ${isOverridden ? '<span class="cell-overridden-badge" title="Manually overridden"></span>' : ''}
          <div class="cell-content leading-relaxed">
            ${hasContent 
              ? `<div class="text-xs text-slate-100">${escapeHtml(val)}</div>` 
              : `<span class="text-slate-600 italic text-[11px]">${isProcessing ? 'AI processing...' : 'Pending call'}</span>`
            }
          </div>
        </td>
      `;
    });

    // Master Audit Columns
    bodyHtml += `
        <td class="px-4 py-3 whitespace-nowrap border-r border-slate-800/60 align-middle">
          ${isCompleted ? renderSentimentBadge(row._sentiment, row._confidence) : '<span class="text-slate-600 text-xs">—</span>'}
        </td>
        <td class="px-4 py-3 whitespace-nowrap text-center align-middle">
          ${isCompleted 
            ? `<button onclick="openTranscriptDrawer('${row._id}')" class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 transition shadow-sm">
                 <i data-lucide="file-text" class="w-3.5 h-3.5"></i> View Transcript
               </button>`
            : `<button onclick="simulateCallSession('${row._id}')" class="text-[11px] text-slate-500 hover:text-sky-400 transition" title="Quick Demo Simulate">
                 ⚡ Demo Call
               </button>`
          }
        </td>
      </tr>
    `;
  });

  tableBody.innerHTML = bodyHtml;
  lucide.createIcons();
}

// Render Session Control cell content based on row lifecycle
function renderSessionCellContent(row) {
  const isThisRecording = activeRecording.rowId === row._id;

  if (isThisRecording) {
    // Currently Recording on this specific row
    return `
      <div class="w-full flex flex-col gap-1.5 bg-[#090d16] p-2 rounded-lg border border-red-500/40 shadow-lg shadow-red-500/10">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-red-500 rec-dot"></span>
            <span class="text-[11px] font-bold text-red-400 uppercase tracking-wider">
              ${activeRecording.isPaused ? 'HOLD PAUSED' : 'REC'}
            </span>
            <span id="call-timer-${row._id}" class="font-mono text-xs text-white font-bold ml-1">00:00</span>
          </div>
        </div>

        <!-- Live Waveform Visualizer Canvas -->
        <canvas id="canvas-${row._id}" width="210" height="26" class="waveform-canvas rounded bg-black/40 border border-slate-800"></canvas>

        <div class="flex items-center gap-1.5 mt-0.5">
          <!-- Pause / Resume -->
          <button onclick="togglePauseRecording('${row._id}')" id="btn-pause-${row._id}" 
                  class="flex-1 py-1 px-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-semibold flex items-center justify-center gap-1 border border-slate-700">
            <i data-lucide="${activeRecording.isPaused ? 'play' : 'pause'}" class="w-3 h-3 text-amber-400"></i>
            <span>${activeRecording.isPaused ? 'Resume' : 'Pause'}</span>
          </button>

          <!-- Stop & Queue -->
          <button onclick="stopAndQueueRecording('${row._id}')" 
                  class="flex-1 py-1 px-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold flex items-center justify-center gap-1 shadow-sm">
            <i data-lucide="check" class="w-3 h-3"></i>
            <span>Stop & AI</span>
          </button>

          <!-- Cancel -->
          <button onclick="cancelRecording('${row._id}')" 
                  class="p-1 rounded bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-slate-700" title="Discard">
            <i data-lucide="x" class="w-3 h-3"></i>
          </button>
        </div>
      </div>
    `;
  }

  if (row._status === 'queued') {
    return `
      <div class="ai-processing-pill inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30">
        <i data-lucide="clock" class="w-3.5 h-3.5 text-amber-400 animate-spin"></i>
        <span>In AI Queue...</span>
      </div>
    `;
  }

  if (row._status === 'transcribing') {
    return `
      <div class="ai-processing-pill inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/30">
        <i data-lucide="mic" class="w-3.5 h-3.5 text-purple-400 animate-pulse"></i>
        <span>Transcribing...</span>
      </div>
    `;
  }

  if (row._status === 'synthesizing') {
    return `
      <div class="ai-processing-pill inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/30">
        <i data-lucide="brain" class="w-3.5 h-3.5 text-sky-400 animate-bounce"></i>
        <span>Gemini AI Answering...</span>
      </div>
    `;
  }

  if (row._status === 'completed') {
    return `
      <div class="flex items-center gap-1.5">
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <i data-lucide="check-circle" class="w-3 h-3"></i> Done
        </span>
        ${row._audioUrl 
          ? `<button onclick="playRowAudio('${row._audioUrl}')" class="p-1 rounded bg-slate-800 hover:bg-slate-700 text-sky-400 border border-slate-700" title="Listen Audio">
               <i data-lucide="play" class="w-3 h-3"></i>
             </button>`
          : ''
        }
        <button onclick="startCallSession('${row._id}')" class="text-[10px] text-slate-500 hover:text-slate-300 ml-1" title="Re-record Call">
          Re-record
        </button>
      </div>
    `;
  }

  // Idle Default State
  return `
    <div class="flex items-center gap-1.5">
      <!-- Start Microphone Session -->
      <button onclick="startCallSession('${row._id}')" class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 hover:border-sky-400 transition shadow-sm">
        <i data-lucide="mic" class="w-3.5 h-3.5"></i>
        <span>Start Call</span>
      </button>

      <!-- Attach Existing Audio File -->
      <button onclick="triggerRowAudioAttach('${row._id}')" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 transition" title="Attach Audio File">
        <i data-lucide="paperclip" class="w-3.5 h-3.5"></i>
      </button>
    </div>
  `;
}

// Sentiment & Score Badge Helper
function renderSentimentBadge(sentiment, confidence) {
  let badgeClass = 'bg-slate-800 text-slate-300 border-slate-700';
  if (sentiment === 'Positive') badgeClass = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
  else if (sentiment === 'Negative') badgeClass = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
  else if (sentiment === 'Neutral') badgeClass = 'bg-sky-500/10 text-sky-400 border-sky-500/20';

  return `
    <div class="flex items-center gap-2">
      <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${badgeClass}">
        ${sentiment || 'Neutral'}
      </span>
      <span class="text-[10px] text-slate-400 font-mono">${confidence ? `${confidence}%` : ''}</span>
    </div>
  `;
}

// =====================================================================
// ROW-LEVEL WEB AUDIO API RECORDING CONTROLLER
// =====================================================================
async function startCallSession(rowId) {
  // If already recording on another row, stop or prevent conflict
  if (activeRecording.rowId) {
    if (activeRecording.rowId === rowId) return;
    const confirmSwitch = confirm("Another call session is currently active. Would you like to stop it and start this new call?");
    if (!confirmSwitch) return;
    await stopAndQueueRecording(activeRecording.rowId);
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    const audioContext = new AudioContextClass();
    const sourceNode = audioContext.createMediaStreamSource(stream);
    
    // Dynamics Compressor for crisp phone audio clarity
    const compressor = audioContext.createDynamicsCompressor();
    compressor.threshold.setValueAtTime(-30, audioContext.currentTime);
    compressor.knee.setValueAtTime(40, audioContext.currentTime);
    compressor.ratio.setValueAtTime(12, audioContext.currentTime);
    compressor.attack.setValueAtTime(0, audioContext.currentTime);
    compressor.release.setValueAtTime(0.25, audioContext.currentTime);

    const analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = 64;
    const bufferLength = analyserNode.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    sourceNode.connect(compressor);
    compressor.connect(analyserNode);

    // Setup MediaRecorder
    let mimeType = 'audio/webm;codecs=opus';
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' : 'audio/webm';
    }

    const mediaRecorder = new MediaRecorder(stream, { mimeType });
    const chunks = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunks.push(e.data);
    };

    activeRecording = {
      rowId,
      stream,
      mediaRecorder,
      audioContext,
      analyserNode,
      dataArray,
      chunks,
      startTime: Date.now(),
      timerInterval: null,
      animFrameId: null,
      isPaused: false,
      pauseStartTime: 0,
      totalPausedDuration: 0
    };

    mediaRecorder.start(250); // Slice every 250ms

    // Re-render this specific row cell to show recording UI
    renderGrid();

    // Start timer & visualizer
    startRecordingTimer(rowId);
    startWaveformVisualizer(rowId);

  } catch (err) {
    console.error('Failed to access microphone:', err);
    alert(`Microphone Access Error: ${err.message}. Please allow microphone permissions.`);
  }
}

function startRecordingTimer(rowId) {
  const timerEl = document.getElementById(`call-timer-${rowId}`);
  activeRecording.timerInterval = setInterval(() => {
    if (!activeRecording.isPaused && timerEl) {
      const elapsedMs = Date.now() - activeRecording.startTime - activeRecording.totalPausedDuration;
      const totalSec = Math.floor(elapsedMs / 1000);
      const mins = String(Math.floor(totalSec / 60)).padStart(2, '0');
      const secs = String(totalSec % 60).padStart(2, '0');
      timerEl.innerText = `${mins}:${secs}`;
    }
  }, 500);
}

function startWaveformVisualizer(rowId) {
  const canvas = document.getElementById(`canvas-${rowId}`);
  if (!canvas || !activeRecording.analyserNode) return;

  const ctx = canvas.getContext('2d');
  const analyser = activeRecording.analyserNode;
  const dataArray = activeRecording.dataArray;

  function draw() {
    activeRecording.animFrameId = requestAnimationFrame(draw);
    analyser.getByteFrequencyData(dataArray);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (activeRecording.isPaused) {
      ctx.fillStyle = '#f59e0b';
      ctx.font = '10px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('PAUSED (CALL ON HOLD)', canvas.width / 2, canvas.height / 2 + 3);
      return;
    }

    const barWidth = (canvas.width / dataArray.length) * 1.5;
    let x = 0;

    for (let i = 0; i < dataArray.length; i++) {
      const barHeight = (dataArray[i] / 255) * canvas.height;
      
      // Gradient from cyan to purple
      const r = Math.floor(14 + (dataArray[i] / 255) * 125);
      const g = Math.floor(165 + (dataArray[i] / 255) * 40);
      const b = 233;

      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
      x += barWidth;
    }
  }

  draw();
}

function togglePauseRecording(rowId) {
  if (activeRecording.rowId !== rowId || !activeRecording.mediaRecorder) return;

  if (!activeRecording.isPaused) {
    activeRecording.mediaRecorder.pause();
    activeRecording.isPaused = true;
    activeRecording.pauseStartTime = Date.now();
  } else {
    activeRecording.mediaRecorder.resume();
    activeRecording.isPaused = false;
    activeRecording.totalPausedDuration += Date.now() - activeRecording.pauseStartTime;
  }
  renderGrid();
  startRecordingTimer(rowId);
  startWaveformVisualizer(rowId);
}

async function stopAndQueueRecording(rowId) {
  if (activeRecording.rowId !== rowId || !activeRecording.mediaRecorder) return;

  const row = dataset.rows.find(r => r._id === rowId);
  const totalDuration = Math.round((Date.now() - activeRecording.startTime - activeRecording.totalPausedDuration) / 1000);

  // Stop visualizer and timer
  if (activeRecording.animFrameId) cancelAnimationFrame(activeRecording.animFrameId);
  if (activeRecording.timerInterval) clearInterval(activeRecording.timerInterval);

  return new Promise((resolve) => {
    activeRecording.mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(activeRecording.chunks, { type: activeRecording.mediaRecorder.mimeType });

      // Clean up hardware
      if (activeRecording.stream) {
        activeRecording.stream.getTracks().forEach(track => track.stop());
      }
      if (activeRecording.audioContext) {
        activeRecording.audioContext.close();
      }

      // Clear active recording state immediately so UI unlocks for next call!
      activeRecording = {
        rowId: null,
        stream: null,
        mediaRecorder: null,
        audioContext: null,
        analyserNode: null,
        dataArray: null,
        chunks: [],
        startTime: 0,
        timerInterval: null,
        animFrameId: null,
        isPaused: false,
        pauseStartTime: 0,
        totalPausedDuration: 0
      };

      // Set row status to queued immediately in UI
      if (row) row._status = 'queued';
      renderGrid();

      // Dispatch to background processing worker queue via FormData
      const formData = new FormData();
      formData.append('audio', audioBlob, `call-${rowId}.webm`);
      formData.append('duration', totalDuration);

      try {
        const res = await fetch(`/api/records/${rowId}/audio`, {
          method: 'POST',
          body: formData
        });
        const result = await res.json();
        console.log(`[QUEUE] Row ${rowId} submitted to background worker:`, result);
      } catch (err) {
        console.error(`[QUEUE] Error submitting audio for row ${rowId}:`, err);
      }

      resolve();
    };

    activeRecording.mediaRecorder.stop();
  });
}

function cancelRecording(rowId) {
  if (activeRecording.rowId !== rowId) return;

  if (activeRecording.animFrameId) cancelAnimationFrame(activeRecording.animFrameId);
  if (activeRecording.timerInterval) clearInterval(activeRecording.timerInterval);
  if (activeRecording.stream) {
    activeRecording.stream.getTracks().forEach(track => track.stop());
  }
  if (activeRecording.audioContext) {
    activeRecording.audioContext.close();
  }

  activeRecording = {
    rowId: null,
    stream: null,
    mediaRecorder: null,
    audioContext: null,
    analyserNode: null,
    dataArray: null,
    chunks: [],
    startTime: 0,
    timerInterval: null,
    animFrameId: null,
    isPaused: false,
    pauseStartTime: 0,
    totalPausedDuration: 0
  };

  renderGrid();
}

// Quick Demo Simulator
async function simulateCallSession(rowId) {
  const row = dataset.rows.find(r => r._id === rowId);
  if (row) row._status = 'queued';
  renderGrid();

  try {
    const res = await fetch(`/api/records/${rowId}/simulate`, { method: 'POST' });
    const data = await res.json();
    console.log(`[SIMULATE] Enqueued ${rowId}:`, data);
  } catch (err) {
    console.error('Error simulating call session:', err);
  }
}

// Process all idle rows in batch
async function processAllIdleRows() {
  try {
    const res = await fetch('/api/queue/process-all', { method: 'POST' });
    const data = await res.json();
    fetchInitialDataset();
  } catch (err) {
    console.error('Error triggering batch processing:', err);
  }
}

// Attach audio file to row
let targetRowForAttachment = null;
function triggerRowAudioAttach(rowId) {
  targetRowForAttachment = rowId;
  document.getElementById('row-audio-input').click();
}

function setupRowAudioInput() {
  const input = document.getElementById('row-audio-input');
  input.addEventListener('change', async (e) => {
    if (!input.files || input.files.length === 0 || !targetRowForAttachment) return;
    const file = input.files[0];
    const rowId = targetRowForAttachment;

    const row = dataset.rows.find(r => r._id === rowId);
    if (row) row._status = 'queued';
    renderGrid();

    const formData = new FormData();
    formData.append('audio', file);
    formData.append('duration', 60);

    try {
      const res = await fetch(`/api/records/${rowId}/audio`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      console.log(`[ATTACH] File uploaded for ${rowId}:`, data);
    } catch (err) {
      console.error('Error uploading row audio:', err);
    } finally {
      input.value = '';
      targetRowForAttachment = null;
    }
  });
}

function playRowAudio(audioUrl) {
  const audio = new Audio(audioUrl);
  audio.play();
}

// =====================================================================
// LIVE ROW UPDATES (NON-BLOCKING)
// =====================================================================
function updateRowStatusInGrid(rowId, status, label) {
  const row = dataset.rows.find(r => r._id === rowId);
  if (row) row._status = status;

  const cell = document.getElementById(`session-cell-${rowId}`);
  if (cell) {
    cell.innerHTML = renderSessionCellContent(row || { _id: rowId, _status: status });
    lucide.createIcons();
  }
}

function updateCompletedRowInGrid(updatedRow) {
  const rowEl = document.getElementById(`row-${updatedRow._id}`);
  if (rowEl) {
    rowEl.classList.add('row-highlight-completed');
    setTimeout(() => rowEl.classList.remove('row-highlight-completed'), 3000);
  }
  renderGrid();
}

// =====================================================================
// DOUBLE-CLICK INLINE EDITING (DATA INTEGRITY & OVERRIDE)
// =====================================================================
function startCellEdit(rowId, column, cellEl) {
  // If already editing, return
  if (cellEl.querySelector('textarea')) return;

  const row = dataset.rows.find(r => r._id === rowId);
  if (!row) return;

  const currentValue = row[column] || '';
  const cellContentDiv = cellEl.querySelector('.cell-content');

  cellContentDiv.innerHTML = `
    <div class="space-y-1.5" onclick="event.stopPropagation()">
      <textarea id="edit-input-${rowId}" 
                class="w-full p-2 text-xs bg-slate-900 border border-sky-500 rounded-lg text-white font-sans focus:outline-none shadow-xl custom-scrollbar" 
                rows="3">${escapeHtml(currentValue)}</textarea>
      <div class="flex items-center justify-end gap-1.5">
        <button onclick="cancelCellEdit('${rowId}', '${escapeAttr(column)}', this.closest('.editable-cell'))" 
                class="px-2 py-1 text-[10px] text-slate-400 hover:text-white rounded bg-slate-800">
          Cancel (Esc)
        </button>
        <button onclick="saveCellEdit('${rowId}', '${escapeAttr(column)}', this.closest('.editable-cell'))" 
                class="px-2.5 py-1 text-[10px] font-bold text-white rounded bg-sky-500 hover:bg-sky-400 shadow-sm">
          Save (Enter)
        </button>
      </div>
    </div>
  `;

  const textarea = cellContentDiv.querySelector('textarea');
  textarea.focus();
  textarea.select();

  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      saveCellEdit(rowId, column, cellEl);
    } else if (e.key === 'Escape') {
      cancelCellEdit(rowId, column, cellEl);
    }
  });
}

async function saveCellEdit(rowId, column, cellEl) {
  const textarea = cellEl.querySelector('textarea');
  if (!textarea) return;

  const newValue = textarea.value.trim();
  const row = dataset.rows.find(r => r._id === rowId);

  try {
    const res = await fetch(`/api/rows/${rowId}/cell`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ column, value: newValue })
    });
    const result = await res.json();
    if (result.success && row) {
      row[column] = newValue;
      if (!row._overriddenFields) row._overriddenFields = {};
      row._overriddenFields[column] = result.overriddenMeta;
    }
  } catch (err) {
    console.error('Error saving cell edit:', err);
  } finally {
    renderGrid();
  }
}

function cancelCellEdit(rowId, column, cellEl) {
  renderGrid();
}

// =====================================================================
// MASTER TRANSCRIPT & AUDIT SLIDE-OVER DRAWER
// =====================================================================
function openTranscriptDrawer(rowId) {
  const row = dataset.rows.find(r => r._id === rowId);
  if (!row) return;

  selectedRowForDrawer = row;

  // Set Subtitle & Badges
  const customerName = row.Customer_Name || row.Consumer_Name || row.Participant_Name || 'Consumer';
  const city = row.City || row.Region || row.State || '';
  const sku = row.Product_SKU || row.Product_Variant || '';
  document.getElementById('drawer-customer-subtitle').innerText = `${customerName} · ${city} · ${sku}`;

  // Sentiment Badge
  const sentimentBadge = document.getElementById('drawer-sentiment-badge');
  sentimentBadge.innerText = row._sentiment || 'Neutral';
  sentimentBadge.className = `px-2 py-0.5 rounded text-[10px] font-semibold border ${
    row._sentiment === 'Positive' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
    row._sentiment === 'Negative' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
    'bg-sky-500/10 text-sky-400 border-sky-500/20'
  }`;

  // Audio Player
  const audioContainer = document.getElementById('drawer-audio-container');
  const audioElement = document.getElementById('drawer-audio-element');
  const durationEl = document.getElementById('drawer-audio-duration');

  if (row._audioUrl) {
    audioContainer.classList.remove('hidden');
    audioElement.src = row._audioUrl;
    durationEl.innerText = `${row._audioDuration || 60}s duration`;
  } else {
    audioContainer.classList.add('hidden');
  }

  // Summary
  document.getElementById('drawer-summary-text').innerText = row._summary || 'No call summary recorded yet.';

  // Verbatim Dialogue List
  const dialogueList = document.getElementById('drawer-dialogue-list');
  dialogueList.innerHTML = renderFormattedDialogue(row._transcript);

  // Extracted Insights List
  const insightsList = document.getElementById('drawer-extracted-insights');
  let insightsHtml = '';
  dataset.insightColumns.forEach(col => {
    const val = row[col] || 'Not discussed';
    insightsHtml += `
      <div class="p-3 rounded-lg bg-slate-900 border border-slate-800/80">
        <div class="text-[11px] font-semibold text-teal-400 mb-1">${escapeHtml(col)}</div>
        <div class="text-xs text-slate-200 leading-relaxed">${escapeHtml(val)}</div>
      </div>
    `;
  });
  insightsList.innerHTML = insightsHtml;

  // Show Drawer
  document.getElementById('transcript-drawer').classList.remove('translate-x-full');
  document.getElementById('drawer-backdrop').classList.remove('hidden');
  lucide.createIcons();
}

function closeTranscriptDrawer() {
  document.getElementById('transcript-drawer').classList.add('translate-x-full');
  document.getElementById('drawer-backdrop').classList.add('hidden');
  const audioElement = document.getElementById('drawer-audio-element');
  if (audioElement) audioElement.pause();
  selectedRowForDrawer = null;
}

function renderFormattedDialogue(rawTranscript) {
  if (!rawTranscript || rawTranscript.trim() === '') {
    return `<div class="p-4 text-center text-xs text-slate-500 bg-slate-900/50 rounded-lg">No dialogue transcript available.</div>`;
  }

  const lines = rawTranscript.split('\n').filter(l => l.trim() !== '');
  let html = '';

  lines.forEach(line => {
    const isAgent = line.includes('[Elaya Narayanan]') || line.startsWith('Agent:');
    const isCustomer = line.includes('[Customer]') || line.startsWith('Customer:');
    
    const cleanText = line
      .replace(/^\[Strategic Agent\]:\s*/i, '')
      .replace(/^\[Customer\]:\s*/i, '')
      .replace(/^Agent:\s*/i, '')
      .replace(/^Customer:\s*/i, '');

    if (isAgent) {
      html += `
        <div class="flex items-start gap-2.5">
          <div class="w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
            AG
          </div>
          <div class="flex-1 bg-sky-950/20 border border-sky-500/20 rounded-xl rounded-tl-none p-3 text-xs text-sky-100 leading-relaxed">
            <span class="text-[10px] font-bold uppercase tracking-wider text-sky-400 block mb-0.5">Elaya Narayanan / Interviewer</span>
            ${escapeHtml(cleanText)}
          </div>
        </div>
      `;
    } else if (isCustomer) {
      html += `
        <div class="flex items-start gap-2.5 flex-row-reverse">
          <div class="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
            CU
          </div>
          <div class="flex-1 bg-emerald-950/20 border border-emerald-500/20 rounded-xl rounded-tr-none p-3 text-xs text-emerald-100 leading-relaxed">
            <span class="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block mb-0.5 text-right">Customer</span>
            ${escapeHtml(cleanText)}
          </div>
        </div>
      `;
    } else {
      html += `
        <div class="p-2 text-xs text-slate-400 italic bg-slate-900/60 rounded-lg">
          ${escapeHtml(line)}
        </div>
      `;
    }
  });

  return html;
}

// Edit Transcript Notes
async function editCurrentTranscript() {
  if (!selectedRowForDrawer) return;

  const newNotes = prompt('Edit / Add Master Transcript Notes:', selectedRowForDrawer._transcript);
  if (newNotes === null) return;

  try {
    const res = await fetch(`/api/rows/${selectedRowForDrawer._id}/transcript`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript: newNotes })
    });
    const result = await res.json();
    if (result.success) {
      selectedRowForDrawer._transcript = newNotes;
      document.getElementById('drawer-dialogue-list').innerHTML = renderFormattedDialogue(newNotes);
      renderGrid();
    }
  } catch (err) {
    console.error('Error updating transcript notes:', err);
  }
}

// =====================================================================
// FILE INTAKE & PRESETS
// =====================================================================
function setupDragAndDrop() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  dropZone.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-sky-500', 'bg-slate-900');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-sky-500', 'bg-slate-900');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-sky-500', 'bg-slate-900');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleSpreadsheetUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files.length > 0) {
      handleSpreadsheetUpload(fileInput.files[0]);
    }
  });

  document.getElementById('btn-open-upload').addEventListener('click', () => {
    document.getElementById('upload-modal').classList.remove('hidden');
  });
}

async function handleSpreadsheetUpload(file) {
  const statusEl = document.getElementById('upload-status');
  statusEl.classList.remove('hidden');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const result = await res.json();
    if (result.success) {
      dataset = result.dataset;
      closeUploadModal();
      updateStatsUI();
      renderGrid();
    } else {
      alert(`Upload Error: ${result.error}`);
    }
  } catch (err) {
    alert(`Network Error: ${err.message}`);
  } finally {
    statusEl.classList.add('hidden');
  }
}

function closeUploadModal() {
  document.getElementById('upload-modal').classList.add('hidden');
}

// Load Presets
async function loadSamplePreset(presetName) {
  try {
    const res = await fetch(`/api/samples/${presetName}`, { method: 'POST' });
    const result = await res.json();
    if (result.success) {
      dataset = result.dataset;
      updateStatsUI();
      renderGrid();
    }
  } catch (err) {
    console.error('Error loading preset:', err);
  }
}

// =====================================================================
// SCHEMA CLASSIFIER MODAL (BASE VS INSIGHTS)
// =====================================================================
function openSchemaModal() {
  const listEl = document.getElementById('column-classification-list');
  const allColumns = [...dataset.baseColumns, ...dataset.insightColumns];

  let html = '';
  allColumns.forEach(col => {
    const isInsight = dataset.insightColumns.includes(col);
    html += `
      <div class="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800">
        <div>
          <div class="text-xs font-semibold text-white">${escapeHtml(col)}</div>
          <div class="text-[10px] text-slate-400">${isInsight ? 'AI Question Header' : 'Customer Attribute'}</div>
        </div>
        <select onchange="tempClassifyColumn('${escapeAttr(col)}', this.value)" 
                class="text-xs rounded-lg px-2.5 py-1 bg-slate-800 border border-slate-700 text-slate-200">
          <option value="base" ${!isInsight ? 'selected' : ''}>Base Information (Read-only)</option>
          <option value="insight" ${isInsight ? 'selected' : ''}>Insight Question (AI Fills)</option>
        </select>
      </div>
    `;
  });

  listEl.innerHTML = html;
  document.getElementById('schema-modal').classList.remove('hidden');
  lucide.createIcons();
}

let tempClassification = {};
function tempClassifyColumn(col, type) {
  tempClassification[col] = type;
}

async function saveSchemaClassification() {
  const newBase = [];
  const newInsight = [];
  const allColumns = [...dataset.baseColumns, ...dataset.insightColumns];

  allColumns.forEach(col => {
    const targetType = tempClassification[col] !== undefined 
      ? tempClassification[col] 
      : (dataset.insightColumns.includes(col) ? 'insight' : 'base');

    if (targetType === 'insight') newInsight.push(col);
    else newBase.push(col);
  });

  try {
    const res = await fetch('/api/schema/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ baseColumns: newBase, insightColumns: newInsight })
    });
    const result = await res.json();
    if (result.success) {
      dataset = result.dataset;
      closeSchemaModal();
      renderGrid();
    }
  } catch (err) {
    console.error('Error saving schema classification:', err);
  }
}

function closeSchemaModal() {
  document.getElementById('schema-modal').classList.add('hidden');
  tempClassification = {};
}

// =====================================================================
// SETTINGS & GEMINI API KEY
// =====================================================================
async function openSettingsModal() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    const statusEl = document.getElementById('api-key-status');
    if (data.hasApiKey) {
      statusEl.innerHTML = `<i data-lucide="check" class="w-3 h-3 text-emerald-400"></i> Active Key (${data.keyMasked})`;
      statusEl.className = 'mt-1.5 text-[11px] text-emerald-400 flex items-center gap-1';
    } else {
      statusEl.innerHTML = `<i data-lucide="alert-circle" class="w-3 h-3 text-amber-400"></i> Offline Simulation Mode Active`;
      statusEl.className = 'mt-1.5 text-[11px] text-amber-400 flex items-center gap-1';
    }
    lucide.createIcons();
  } catch (err) {}
  document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettingsModal() {
  document.getElementById('settings-modal').classList.add('hidden');
}

async function saveSettings() {
  const apiKey = document.getElementById('input-api-key').value;
  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ apiKey })
    });
    closeSettingsModal();
    alert('Settings successfully updated!');
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

// Search Handler
function setupSearch() {
  const searchInput = document.getElementById('grid-search');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      renderGrid();
    });
  }

  const meetingSearchInput = document.getElementById('meeting-search');
  if (meetingSearchInput) {
    meetingSearchInput.addEventListener('input', () => {
      renderMeetingsList();
    });
  }
}

// Utility Helpers
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeAttr(str) {
  if (!str) return '';
  return String(str).replace(/"/g, '&quot;').replace(/'/g, "\\'");
}

// =====================================================================
// DATASET EXPORT & PERSISTENCE ENGINE
// =====================================================================
async function exportDataset(format) {
  const exportBtn = document.getElementById('btn-export-main');
  const originalHtml = exportBtn ? exportBtn.innerHTML : '';
  if (exportBtn) {
    exportBtn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Exporting...`;
    lucide.createIcons();
  }

  showToast(`Preparing ${format.toUpperCase()} export with all transcripts & AI answers...`, 'info');

  try {
    if (IS_STANDALONE || !window.location.port) {
      // Standalone Browser Export with SheetJS
      const rowsForExport = dataset.rows.map(r => {
        const out = {};
        dataset.baseColumns.forEach(c => { out[c] = r[c] || ''; });
        dataset.insightColumns.forEach(c => { out[c] = r[c] || ''; });
        out['AI_Status'] = r._status || 'idle';
        out['AI_Confidence'] = r._confidence ? `${r._confidence}%` : '';
        out['AI_Executive_Summary'] = r._summary || '';
        out['Master_Verbatim_Transcript'] = r._transcript || '';
        return out;
      });

      const cleanBase = (dataset.fileName || 'ElayaNarayanan_AudioCRM')
        .replace(/\.[^/.]+$/, '')
        .replace(/[^a-zA-Z0-9_\-]/g, '_');
      const timeStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const filename = `${cleanBase}_Insights_Export_${timeStr}.${format === 'csv' ? 'csv' : 'xlsx'}`;

      const ws = XLSX.utils.json_to_sheet(rowsForExport);

      if (format === 'csv') {
        const csvText = XLSX.utils.sheet_to_csv(ws);
        const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => { window.URL.revokeObjectURL(url); a.remove(); }, 1000);
      } else {
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Discussion_Insights");
        XLSX.writeFile(wb, filename);
      }

      showToast(`✓ ${filename} successfully downloaded!`, 'success');
      return;
    }

    const res = await fetch(`/api/export/${format}`);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Export failed (${res.status}): ${errText}`);
    }

    const blob = await res.blob();
    const cleanBase = (dataset.fileName || 'ElayaNarayanan_AudioCRM')
      .replace(/\.[^/.]+$/, '')
      .replace(/[^a-zA-Z0-9_\-]/g, '_')
      .replace(/_+/g, '_');
    const timeStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const filename = `${cleanBase}_Insights_Export_${timeStr}.${format === 'csv' ? 'csv' : 'xlsx'}`;

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();

    setTimeout(() => {
      window.URL.revokeObjectURL(url);
      a.remove();
    }, 1500);

    showToast(`✓ ${filename} successfully downloaded!`, 'success');
  } catch (err) {
    console.error('Export error:', err);
    showToast(`Export Notice: Direct download triggering...`, 'info');
    // Fallback: direct browser trigger
    window.location.href = `/api/export/${format}`;
  } finally {
    if (exportBtn) {
      exportBtn.innerHTML = originalHtml;
      lucide.createIcons();
    }
  }
}

async function saveDatasetSnapshot() {
  const saveText = document.getElementById('save-status-text');
  if (saveText) saveText.innerText = 'Saving...';

  try {
    localStorage.setItem('elaya_audiocrm_dataset', JSON.stringify(dataset));
    if (IS_STANDALONE) {
      const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      if (saveText) saveText.innerText = `Saved (${time})`;
      showToast(`✓ Dataset saved to browser storage! (${dataset.rows.length} rows)`, 'success');
      setTimeout(() => { if (saveText) saveText.innerText = 'Save Snapshot'; }, 3500);
      return;
    }
    const res = await fetch('/api/dataset/save', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      if (saveText) saveText.innerText = `Saved (${time})`;
      showToast(`✓ Dataset saved to disk! (${data.totalRows} rows, ${data.completedRows} completed)`, 'success');
      setTimeout(() => {
        if (saveText) saveText.innerText = 'Save Snapshot';
      }, 3500);
    } else {
      throw new Error(data.error || 'Failed to save');
    }
  } catch (err) {
    console.error('Save error:', err);
    if (saveText) saveText.innerText = 'Save Failed';
    showToast(`Save error: ${err.message}`, 'error');
  }
}

function downloadBackupJson() {
  showToast('Downloading complete raw JSON session backup...', 'info');
  window.location.href = '/api/dataset/backup';
}

function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none max-w-sm';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bgColor = type === 'success' ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200' :
                  type === 'error' ? 'bg-rose-950/90 border-rose-500/40 text-rose-200' :
                  'bg-slate-900/90 border-sky-500/40 text-sky-200';

  toast.className = `${bgColor} border px-4 py-2.5 rounded-xl text-xs font-semibold shadow-2xl backdrop-blur-md flex items-center gap-2 pointer-events-auto transform translate-y-3 transition-all duration-200 ease-out`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;

  toastContainer.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-3');
    toast.classList.add('translate-y-0');
  });

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// =====================================================================
// WORKSPACE NAVIGATION & WELCOME PORTAL CONTROLLER
// =====================================================================
let currentAppMode = 'audiocrm';

function initPortalMode() {
  const savedMode = localStorage.getItem('elaya_app_mode');
  if (savedMode === 'meetings' || savedMode === 'audiocrm') {
    switchAppMode(savedMode, false);
  } else {
    // Show welcoming modal on initial arrival
    openPortalModal();
  }
}

function openPortalModal() {
  const modal = document.getElementById('portal-modal');
  if (modal) modal.classList.remove('hidden');
}

function closePortalModal() {
  const modal = document.getElementById('portal-modal');
  if (modal) modal.classList.add('hidden');
}

function selectPortalMode(mode) {
  localStorage.setItem('elaya_app_mode', mode);
  switchAppMode(mode, true);
  closePortalModal();
}

function switchAppMode(mode, showFeedback = true) {
  currentAppMode = mode;
  const tabAudiocrm = document.getElementById('tab-audiocrm');
  const tabMeetings = document.getElementById('tab-meetings');
  const viewAudiocrm = document.getElementById('view-audiocrm');
  const viewMeetings = document.getElementById('view-meetings');
  const audiocrmActions = document.getElementById('audiocrm-actions');
  const meetingsActions = document.getElementById('meetings-actions');

  if (mode === 'meetings') {
    if (viewAudiocrm) viewAudiocrm.classList.add('hidden');
    if (viewMeetings) viewMeetings.classList.remove('hidden');
    if (audiocrmActions) audiocrmActions.classList.add('hidden');
    if (meetingsActions) meetingsActions.classList.remove('hidden');

    if (tabMeetings) {
      tabMeetings.className = 'flex items-center gap-2 px-3.5 py-1.5 text-xs font-bold rounded-lg transition duration-150 text-white bg-teal-500 shadow-md shadow-teal-500/25';
    }
    if (tabAudiocrm) {
      tabAudiocrm.className = 'flex items-center gap-2 px-3.5 py-1.5 text-xs font-bold rounded-lg transition duration-150 text-slate-400 hover:text-slate-200';
    }
    fetchMeetings();
    if (showFeedback) showToast('Switched to In-Person Meeting Intelligence', 'info');
  } else {
    // audiocrm
    if (viewMeetings) viewMeetings.classList.add('hidden');
    if (viewAudiocrm) viewAudiocrm.classList.remove('hidden');
    if (meetingsActions) meetingsActions.classList.add('hidden');
    if (audiocrmActions) audiocrmActions.classList.remove('hidden');

    if (tabAudiocrm) {
      tabAudiocrm.className = 'flex items-center gap-2 px-3.5 py-1.5 text-xs font-bold rounded-lg transition duration-150 text-white bg-sky-500 shadow-md shadow-sky-500/25';
    }
    if (tabMeetings) {
      tabMeetings.className = 'flex items-center gap-2 px-3.5 py-1.5 text-xs font-bold rounded-lg transition duration-150 text-slate-400 hover:text-slate-200';
    }
    if (showFeedback) showToast('Switched to Customer AudioCRM & KYC Engine', 'info');
  }
}

// =====================================================================
// IN-PERSON MEETING DISCUSSION INTELLIGENCE CONTROLLER
// Continuous Hours-Long Recording · Seamless 10-Minute Rolling Chunks
// =====================================================================
let meetingsList = [];
let activeMeetingSession = null;
let selectedMeetingForModal = null;

function showActiveMeetingView() {
  const recView = document.getElementById('meeting-recorder-view');
  const arcView = document.getElementById('meeting-archive-view');
  const btnRec = document.getElementById('btn-show-active-meeting');
  const btnArc = document.getElementById('btn-show-archive');

  if (recView) recView.classList.remove('hidden');
  if (arcView) arcView.classList.add('hidden');

  if (btnRec) {
    btnRec.className = 'px-3.5 py-1.5 text-xs font-bold rounded-lg bg-teal-500 text-white shadow-md shadow-teal-500/20';
  }
  if (btnArc) {
    btnArc.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700';
  }
}

function showMeetingLibrary() {
  const recView = document.getElementById('meeting-recorder-view');
  const arcView = document.getElementById('meeting-archive-view');
  const btnRec = document.getElementById('btn-show-active-meeting');
  const btnArc = document.getElementById('btn-show-archive');

  if (recView) recView.classList.add('hidden');
  if (arcView) arcView.classList.remove('hidden');

  if (btnArc) {
    btnArc.className = 'px-3.5 py-1.5 text-xs font-bold rounded-lg bg-indigo-600 text-white shadow-md shadow-indigo-600/20';
  }
  if (btnRec) {
    btnRec.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700';
  }

  fetchMeetings();
}

async function fetchMeetings() {
  const cached = localStorage.getItem('elaya_meetings_list');
  if (cached) {
    try {
      const list = JSON.parse(cached);
      if (Array.isArray(list) && list.length > 0) {
        meetingsList = list;
        const badge = document.getElementById('meeting-count-badge');
        if (badge) badge.innerText = meetingsList.length;
        renderMeetingsList();
        if (IS_STANDALONE) return;
      }
    } catch (e) {}
  }

  try {
    const endpoint = IS_STANDALONE ? './data/meetings.json' : '/api/meetings';
    const res = await fetch(endpoint);
    const data = await res.json();
    const list = data.meetings || data;
    if (Array.isArray(list)) {
      meetingsList = list;
      const badge = document.getElementById('meeting-count-badge');
      if (badge) badge.innerText = meetingsList.length;
      renderMeetingsList();
      return;
    }
  } catch (err) {
    console.warn('Meetings API unavailable, trying static fallback:', err);
  }

  try {
    const res2 = await fetch('data/meetings.json');
    const list2 = await res2.json();
    if (Array.isArray(list2)) {
      meetingsList = list2;
      const badge = document.getElementById('meeting-count-badge');
      if (badge) badge.innerText = meetingsList.length;
      renderMeetingsList();
    }
  } catch (e) {}
}

function renderMeetingsList() {
  const grid = document.getElementById('meetings-list-grid');
  if (!grid) return;

  const searchEl = document.getElementById('meeting-search');
  const query = searchEl ? searchEl.value.trim().toLowerCase() : '';

  const filtered = meetingsList.filter(m => {
    if (!query) return true;
    return (m.title && m.title.toLowerCase().includes(query)) ||
           (m.category && m.category.toLowerCase().includes(query)) ||
           (m.summaryPreview && m.summaryPreview.toLowerCase().includes(query)) ||
           (m.attendees && m.attendees.some(a => a.toLowerCase().includes(query)));
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full py-16 text-center text-slate-500">
        <i data-lucide="archive-x" class="w-10 h-10 mx-auto mb-2 opacity-40"></i>
        <div class="text-sm font-semibold text-slate-400">No Discussion Sessions Found</div>
        <p class="text-xs text-slate-500 mt-1">Record a new meeting or clear your search filter.</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  grid.innerHTML = filtered.map(m => {
    const durationMin = Math.round((m.duration || 0) / 60);
    const durationText = durationMin >= 60 ? `${Math.floor(durationMin / 60)}h ${durationMin % 60}m` : `${durationMin} mins`;
    const attendeesText = m.attendees ? m.attendees.join(', ') : 'Elaya Narayanan & Strategy Team';
    
    return `
      <div class="group bg-[#111827] border border-slate-800 hover:border-slate-700 rounded-2xl p-5 shadow-xl transition-all duration-200 flex flex-col justify-between">
        <div>
          <!-- Header Tags -->
          <div class="flex items-center justify-between gap-2 mb-3">
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">
              ${escapeHtml(m.category || 'Discussion')}
            </span>
            <div class="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
              <span>${escapeHtml(m.date || '')}</span>
              <span>·</span>
              <span class="text-teal-300 font-semibold">${durationText}</span>
            </div>
          </div>

          <!-- Meeting Title -->
          <h3 onclick="openMeetingDetails('${m.id}')" class="text-sm font-bold text-white hover:text-teal-300 transition cursor-pointer line-clamp-2 mb-2">
            ${escapeHtml(m.title)}
          </h3>

          <!-- Attendees -->
          <div class="text-[11px] text-slate-400 flex items-center gap-1.5 mb-3 line-clamp-1">
            <i data-lucide="users" class="w-3.5 h-3.5 text-slate-500 shrink-0"></i>
            <span class="truncate">${escapeHtml(attendeesText)}</span>
          </div>

          <!-- Summary Snippet -->
          <p class="text-xs text-slate-300/80 leading-relaxed line-clamp-3 mb-4 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80">
            ${escapeHtml(m.summaryPreview || 'Minutes recorded. Click below to inspect details.')}
          </p>

          <!-- Badges for Chunks and Actions -->
          <div class="flex items-center gap-2 mb-4">
            <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">
              ${m.segmentCount || 1} Chunks (10m each)
            </span>
            <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
              ${m.actionItemsCount || 0} Action Items
            </span>
          </div>
        </div>

        <!-- Card Footer Actions -->
        <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
          <button onclick="openMeetingDetails('${m.id}')" class="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 transition">
            <i data-lucide="eye" class="w-3.5 h-3.5"></i> Review Minutes
          </button>
          
          <div class="flex items-center gap-1">
            <button onclick="quickDownloadMeeting('${m.id}', 'md')" class="p-1.5 rounded-lg text-slate-400 hover:text-sky-400 hover:bg-slate-800 transition" title="Download Markdown (.md)">
              <i data-lucide="file-code" class="w-4 h-4"></i>
            </button>
            <button onclick="quickDownloadMeeting('${m.id}', 'txt')" class="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition" title="Download Plain Text (.txt)">
              <i data-lucide="file-text" class="w-4 h-4"></i>
            </button>
            <button onclick="deleteMeeting('${m.id}')" class="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition" title="Delete Session">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  lucide.createIcons();
}

function openNewMeetingModal() {
  showActiveMeetingView();
  const titleInput = document.getElementById('live-meeting-title');
  if (titleInput) {
    titleInput.value = `Executive Strategic Review — ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
    titleInput.focus();
  }
  showToast('Ready to start a new discussion recording session.', 'info');
}

// =====================================================================
// LIVE RECORDING WITH SEAMLESS ROLLING 10-MINUTE CHUNKS
// =====================================================================
async function startMeetingRecording() {
  if (activeMeetingSession && activeMeetingSession.isRecording) {
    showToast('A meeting session is already actively recording!', 'error');
    return;
  }

  const titleEl = document.getElementById('live-meeting-title');
  const catEl = document.getElementById('live-meeting-category');
  const attEl = document.getElementById('live-meeting-attendees');

  const title = titleEl ? titleEl.value.trim() : 'Executive Discussion Session';
  const category = catEl ? catEl.value : 'General';
  const attendees = attEl ? attEl.value.split(',').map(s => s.trim()).filter(Boolean) : [];

  showToast('Initializing high-fidelity meeting audio capture...', 'info');

  try {
    // 1. Create meeting session on backend
    const res = await fetch('/api/meetings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, category, attendees })
    });
    const data = await res.json();
    if (!data.success || !data.meeting) {
      throw new Error(data.error || 'Could not initiate meeting session');
    }

    const meeting = data.meeting;

    // 2. Request user microphone
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 48000,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    // 3. Audio Context & Waveform Visualizer
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const sourceNode = audioContext.createMediaStreamSource(stream);
    const analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = 256;
    sourceNode.connect(analyserNode);

    const dataArray = new Uint8Array(analyserNode.frequencyBinCount);
    const canvas = document.getElementById('meeting-waveform');
    const canvasCtx = canvas ? canvas.getContext('2d') : null;

    let animFrameId = null;
    function renderWaveform() {
      if (!activeMeetingSession || !activeMeetingSession.isRecording) return;
      animFrameId = requestAnimationFrame(renderWaveform);

      analyserNode.getByteFrequencyData(dataArray);
      if (canvasCtx && canvas) {
        canvasCtx.fillStyle = 'rgba(10, 15, 26, 0.4)';
        canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / dataArray.length) * 2.2;
        let x = 0;

        for (let i = 0; i < dataArray.length; i++) {
          const barHeight = (dataArray[i] / 255) * canvas.height;
          canvasCtx.fillStyle = `rgb(20, ${180 + Math.floor(barHeight * 2)}, ${200 + Math.floor(barHeight)})`;
          canvasCtx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
          x += barWidth;
        }
      }
    }
    renderWaveform();

    // 4. MediaRecorder with cross-browser support
    let mimeType = 'audio/webm;codecs=opus';
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mimeType = 'audio/ogg;codecs=opus';
      } else {
        mimeType = '';
      }
    }

    const mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

    activeMeetingSession = {
      id: meeting.id,
      meeting: meeting,
      isRecording: true,
      isPaused: false,
      stream,
      mediaRecorder,
      audioContext,
      analyserNode,
      animFrameId,
      currentSegmentIndex: 1,
      startTime: Date.now(),
      elapsedSeconds: 0,
      segmentStartTime: Date.now(),
      timerInterval: null,
      chunkInterval: null,
      currentSegmentChunks: []
    };

    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0 && activeMeetingSession) {
        activeMeetingSession.currentSegmentChunks.push(event.data);
      }
    };

    // Start recording continuously
    mediaRecorder.start(3000); // chunk slice every 3 seconds into buffer

    // 5. Setup Clock Timer (1 sec interval)
    activeMeetingSession.timerInterval = setInterval(() => {
      if (!activeMeetingSession || activeMeetingSession.isPaused) return;
      activeMeetingSession.elapsedSeconds++;
      updateMeetingClockUI(activeMeetingSession.elapsedSeconds);
    }, 1000);

    // 6. Setup 10-Minute Seamless Auto-Chunk Interval (600,000 ms)
    // Seamless rolling chunking: calling requestData() triggers ondataavailable
    // without stopping or restarting the MediaRecorder! Zero audio dropout!
    activeMeetingSession.chunkInterval = setInterval(() => {
      syncMeetingSegment(false);
    }, 10 * 60 * 1000);

    // 7. Update UI
    updateRecorderControlsUI('recording');
    document.getElementById('transcript-segment-count').innerText = 'Recording Segment #1...';
    document.getElementById('live-meeting-transcript').innerHTML = `
      <div class="flex items-center gap-3 p-4 bg-teal-500/10 border border-teal-500/20 rounded-xl text-teal-300 text-xs animate-pulse">
        <i data-lucide="radio" class="w-4 h-4 text-teal-400"></i>
        <span>Meeting recording active. Dialogue across team members is continuously buffered and transcribed in 10-minute rolling segments.</span>
      </div>
    `;
    lucide.createIcons();

    showToast(`✓ In-person meeting recording started! ID: ${meeting.id}`, 'success');

  } catch (err) {
    console.error('Failed to start meeting recording:', err);
    showToast(`Microphone error: ${err.message}`, 'error');
  }
}

function updateMeetingClockUI(totalSec) {
  const clockEl = document.getElementById('meeting-clock');
  if (!clockEl) return;

  const hrs = Math.floor(totalSec / 3600).toString().padStart(2, '0');
  const mins = Math.floor((totalSec % 3600) / 60).toString().padStart(2, '0');
  const secs = (totalSec % 60).toString().padStart(2, '0');
  clockEl.innerText = `${hrs}:${mins}:${secs}`;

  const segEl = document.getElementById('meeting-current-segment');
  if (segEl && activeMeetingSession) {
    segEl.innerText = activeMeetingSession.currentSegmentIndex;
  }
}

function updateRecorderControlsUI(state) {
  const recPill = document.getElementById('meeting-rec-pill');
  const recDot = document.getElementById('meeting-rec-dot');
  const recText = document.getElementById('meeting-rec-text');

  const btnStart = document.getElementById('btn-start-meeting');
  const btnPause = document.getElementById('btn-pause-meeting');
  const btnSync = document.getElementById('btn-sync-segment');
  const btnFinalize = document.getElementById('btn-finalize-meeting');

  if (state === 'recording') {
    recPill.className = 'flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-rose-500/15 border border-rose-500/40 text-rose-300 text-xs font-bold uppercase tracking-wider';
    recDot.className = 'w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping';
    recText.innerText = 'RECORDING';

    btnStart.classList.add('hidden');
    btnPause.classList.remove('hidden');
    btnPause.innerHTML = `<i data-lucide="pause" class="w-4 h-4 text-amber-400"></i> Pause`;
    btnSync.classList.remove('hidden');
    btnFinalize.classList.remove('hidden');
  } else if (state === 'paused') {
    recPill.className = 'flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-500/15 border border-amber-500/40 text-amber-300 text-xs font-bold uppercase tracking-wider';
    recDot.className = 'w-2.5 h-2.5 rounded-full bg-amber-400';
    recText.innerText = 'PAUSED';

    btnPause.innerHTML = `<i data-lucide="play" class="w-4 h-4 text-emerald-400"></i> Resume`;
  } else {
    // idle / ready
    recPill.className = 'flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-xs font-bold uppercase tracking-wider';
    recDot.className = 'w-2.5 h-2.5 rounded-full bg-slate-500';
    recText.innerText = 'READY';

    btnStart.classList.remove('hidden');
    btnPause.classList.add('hidden');
    btnSync.classList.add('hidden');
    btnFinalize.classList.add('hidden');
  }
  lucide.createIcons();
}

function togglePauseMeeting() {
  if (!activeMeetingSession || !activeMeetingSession.isRecording) return;

  if (activeMeetingSession.isPaused) {
    activeMeetingSession.mediaRecorder.resume();
    activeMeetingSession.isPaused = false;
    updateRecorderControlsUI('recording');
    showToast('Meeting recording resumed.', 'info');
  } else {
    activeMeetingSession.mediaRecorder.pause();
    activeMeetingSession.isPaused = true;
    updateRecorderControlsUI('paused');
    showToast('Meeting recording paused.', 'info');
  }
}

// Force or auto-sync segment (The 10-Minute Rolling Chunker)
async function forceSyncSegment() {
  if (!activeMeetingSession || !activeMeetingSession.isRecording) {
    showToast('No active meeting recording to sync.', 'error');
    return;
  }
  showToast(`Flushing & transcribing Segment #${activeMeetingSession.currentSegmentIndex}...`, 'info');
  await syncMeetingSegment(false);
}

async function syncMeetingSegment(isFinal = false) {
  if (!activeMeetingSession) return;

  const btnSync = document.getElementById('btn-sync-segment');
  const originalHtml = btnSync ? btnSync.innerHTML : '';
  if (btnSync) {
    btnSync.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Processing...`;
    lucide.createIcons();
  }

  try {
    // 1. Force recorder to flush current audio buffer into ondataavailable
    if (activeMeetingSession.mediaRecorder && activeMeetingSession.mediaRecorder.state !== 'inactive') {
      activeMeetingSession.mediaRecorder.requestData();
    }

    // Wait a brief tick for ondataavailable to collect chunks
    await new Promise(r => setTimeout(r, 200));

    const chunks = [...activeMeetingSession.currentSegmentChunks];
    activeMeetingSession.currentSegmentChunks = []; // reset buffer for next rolling segment

    const segmentIndex = activeMeetingSession.currentSegmentIndex;
    const segmentDuration = Math.round((Date.now() - activeMeetingSession.segmentStartTime) / 1000);
    activeMeetingSession.segmentStartTime = Date.now();
    activeMeetingSession.currentSegmentIndex++;

    const audioBlob = chunks.length > 0 ? new Blob(chunks, { type: activeMeetingSession.mediaRecorder.mimeType || 'audio/webm' }) : null;

    const formData = new FormData();
    formData.append('segmentIndex', segmentIndex);
    formData.append('duration', segmentDuration || 600);
    if (audioBlob && audioBlob.size > 0) {
      formData.append('audio', audioBlob, `meeting_${activeMeetingSession.id}_seg_${segmentIndex}.webm`);
    }

    const res = await fetch(`/api/meetings/${activeMeetingSession.id}/segment`, {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (data.success && data.segment) {
      appendSegmentToLiveTranscript(data.segment);
      if (data.meeting) {
        updateLiveDecisionsAndActions(data.meeting);
      }
      showToast(`✓ Segment #${segmentIndex} transcribed & stitched seamlessly!`, 'success');
    }
  } catch (err) {
    console.error('Error syncing meeting segment:', err);
    showToast(`Segment sync error: ${err.message}`, 'error');
  } finally {
    if (btnSync) {
      btnSync.innerHTML = originalHtml;
      lucide.createIcons();
    }
  }
}

function appendSegmentToLiveTranscript(segment) {
  const container = document.getElementById('live-meeting-transcript');
  if (!container) return;

  // Remove placeholder if present
  const placeholder = container.querySelector('.text-center');
  if (placeholder) placeholder.remove();

  const segEl = document.createElement('div');
  segEl.className = 'p-4 bg-slate-900/90 border border-slate-800 rounded-xl space-y-2.5 transition-all';
  segEl.innerHTML = `
    <div class="flex items-center justify-between border-b border-slate-800 pb-2">
      <div class="flex items-center gap-2">
        <span class="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 border border-teal-500/20 font-mono">
          Segment ${segment.index} (${segment.startTime} - ${segment.endTime})
        </span>
        <span class="text-xs font-semibold text-slate-300">Stitched Dialogue</span>
      </div>
      <span class="text-[10px] text-slate-500 font-mono">${Math.round(segment.duration / 60)} mins</span>
    </div>
    <div class="font-sans text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
      ${escapeHtml(segment.transcript)}
    </div>
    ${segment.summary ? `
      <div class="mt-2 pt-2 border-t border-slate-800/80 text-[11px] text-teal-300/90 italic flex items-start gap-1.5">
        <i data-lucide="sparkles" class="w-3.5 h-3.5 shrink-0 text-amber-400 mt-0.5"></i>
        <span><strong>Key Takeaway:</strong> ${escapeHtml(segment.summary)}</span>
      </div>
    ` : ''}
  `;

  container.appendChild(segEl);
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();

  const segCountEl = document.getElementById('transcript-segment-count');
  if (segCountEl) {
    const totalSegments = container.querySelectorAll('.p-4').length;
    segCountEl.innerText = `${totalSegments} Segments Unified`;
  }
}

function updateLiveDecisionsAndActions(meeting) {
  // Update decisions box
  const decBox = document.getElementById('live-meeting-decisions');
  if (decBox && meeting.decisions && meeting.decisions.length > 0) {
    decBox.innerHTML = meeting.decisions.map(d => `
      <div class="p-2.5 bg-slate-900/90 border border-amber-500/20 rounded-xl text-slate-200 flex items-start gap-2">
        <i data-lucide="check" class="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5"></i>
        <span class="leading-snug">${escapeHtml(d)}</span>
      </div>
    `).join('');
  }

  // Update actions box
  const actBox = document.getElementById('live-meeting-actions');
  if (actBox && meeting.actionItems && meeting.actionItems.length > 0) {
    actBox.innerHTML = meeting.actionItems.map(a => `
      <div class="p-2.5 bg-slate-900/90 border border-emerald-500/20 rounded-xl space-y-1">
        <div class="text-slate-200 leading-snug font-medium">${escapeHtml(a.task)}</div>
        <div class="flex items-center gap-2 text-[10px]">
          <span class="text-emerald-400 font-semibold">Owner: ${escapeHtml(a.owner || 'Elaya Narayanan & Strategy Team')}</span>
          <span class="text-slate-500">|</span>
          <span class="text-slate-400">Due: ${escapeHtml(a.deadline || 'Next Sprint')}</span>
        </div>
      </div>
    `).join('');
  }

  lucide.createIcons();
}

async function finalizeActiveMeeting() {
  if (!activeMeetingSession) return;

  const btnFin = document.getElementById('btn-finalize-meeting');
  const origHtml = btnFin ? btnFin.innerHTML : '';
  if (btnFin) {
    btnFin.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Finalizing Minutes...`;
    lucide.createIcons();
  }

  showToast('Synthesizing executive minutes and strategic decisions...', 'info');

  try {
    // 1. Sync final chunk if any
    await syncMeetingSegment(true);

    // 2. Stop audio recording stream and clean up
    if (activeMeetingSession.mediaRecorder && activeMeetingSession.mediaRecorder.state !== 'inactive') {
      activeMeetingSession.mediaRecorder.stop();
    }
    if (activeMeetingSession.stream) {
      activeMeetingSession.stream.getTracks().forEach(t => t.stop());
    }
    if (activeMeetingSession.timerInterval) clearInterval(activeMeetingSession.timerInterval);
    if (activeMeetingSession.chunkInterval) clearInterval(activeMeetingSession.chunkInterval);
    if (activeMeetingSession.animFrameId) cancelAnimationFrame(activeMeetingSession.animFrameId);

    const meetingId = activeMeetingSession.id;

    // 3. Request final synthesis from backend
    const res = await fetch(`/api/meetings/${meetingId}/finalize`, { method: 'POST' });
    const data = await res.json();

    if (data.success && data.meeting) {
      showToast('✓ Meeting successfully finalized & minutes generated!', 'success');
      activeMeetingSession = null;
      updateRecorderControlsUI('ready');
      fetchMeetings();
      // Open detailed minutes modal directly
      openMeetingDetails(meetingId);
    } else {
      throw new Error(data.error || 'Finalization failed');
    }
  } catch (err) {
    console.error('Error finalizing meeting:', err);
    showToast(`Finalize error: ${err.message}`, 'error');
  } finally {
    if (btnFin) {
      btnFin.innerHTML = origHtml;
      lucide.createIcons();
    }
  }
}

// =====================================================================
// MEETING MINUTES MODAL & EXPORTS (MARKDOWN, TEXT, PRINT)
// =====================================================================
async function openMeetingDetails(id) {
  try {
    const res = await fetch(`/api/meetings/${id}`);
    const data = await res.json();
    if (!data.success || !data.meeting) {
      throw new Error('Meeting not found');
    }

    const m = data.meeting;
    selectedMeetingForModal = m;

    const modal = document.getElementById('meeting-modal');
    if (!modal) return;

    // Populate header
    document.getElementById('modal-meeting-category').innerText = m.category || 'General';
    document.getElementById('modal-meeting-title').innerText = m.title;

    const durationMin = Math.round((m.duration || 0) / 60);
    const durationText = durationMin >= 60 ? `${Math.floor(durationMin / 60)}h ${durationMin % 60}m` : `${durationMin} mins`;
    const attendeesText = m.attendees ? m.attendees.join(', ') : 'Elaya Narayanan & Leadership Team';
    document.getElementById('modal-meeting-meta').innerText = `Date: ${m.date || ''} · Duration: ${durationText} · Attendees: ${attendeesText}`;

    // Executive Summary
    const summaryEl = document.getElementById('modal-meeting-summary');
    if (summaryEl) {
      summaryEl.innerHTML = (m.summary || 'Summary pending.')
        .split('\n\n')
        .map(p => `<p>${escapeHtml(p)}</p>`)
        .join('');
    }

    // Decisions
    const decEl = document.getElementById('modal-meeting-decisions');
    if (decEl) {
      if (m.decisions && m.decisions.length > 0) {
        decEl.innerHTML = m.decisions.map(d => `<li class="leading-relaxed"><strong>${escapeHtml(d)}</strong></li>`).join('');
      } else {
        decEl.innerHTML = `<li class="text-slate-500 italic list-none">No explicit decisions logged.</li>`;
      }
    }

    // Action Items
    const actEl = document.getElementById('modal-meeting-actions');
    if (actEl) {
      if (m.actionItems && m.actionItems.length > 0) {
        actEl.innerHTML = m.actionItems.map(a => `
          <div class="p-2.5 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between gap-3">
            <span class="text-slate-200 font-medium">${escapeHtml(a.task)}</span>
            <div class="flex items-center gap-1.5 shrink-0">
              <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">${escapeHtml(a.owner || 'Team')}</span>
              <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">${escapeHtml(a.deadline || 'ASAP')}</span>
            </div>
          </div>
        `).join('');
      } else {
        actEl.innerHTML = `<div class="text-slate-500 italic text-[11px]">No pending action items.</div>`;
      }
    }

    // Master Verbatim Transcript
    const transEl = document.getElementById('modal-meeting-transcript');
    if (transEl) {
      transEl.innerText = m.masterTranscript || 'No transcript available for this discussion.';
    }

    modal.classList.remove('hidden');
    lucide.createIcons();

  } catch (err) {
    console.error('Error opening meeting modal:', err);
    showToast(`Error: ${err.message}`, 'error');
  }
}

function closeMeetingModal() {
  const modal = document.getElementById('meeting-modal');
  if (modal) modal.classList.add('hidden');
}

function downloadMeetingDoc(format) {
  if (!selectedMeetingForModal) return;
  quickDownloadMeeting(selectedMeetingForModal.id, format);
}

function quickDownloadMeeting(meetingId, format) {
  showToast(`Downloading Meeting Minutes as ${format.toUpperCase()}...`, 'info');
  if (IS_STANDALONE) {
    const m = meetingsList.find(x => x.id === meetingId) || selectedMeetingForModal;
    if (!m) return;
    const safeTitle = (m.title || 'Meeting').replace(/[^a-zA-Z0-9_\-]/g, '_');
    if (format === 'md') {
      let md = `# ${m.title}\n\n**Date:** ${m.date} | **Duration:** ${Math.round((m.duration || 0)/60)} mins | **Category:** ${m.category}\n\n**Attendees:** ${m.attendees ? m.attendees.join(', ') : 'Elaya Narayanan & Team'}\n\n---\n\n## 📋 Executive Summary\n\n${m.summary || 'Summary pending.'}\n\n---\n\n`;
      if (m.decisions && m.decisions.length > 0) {
        md += `## 🎯 Strategic Decisions Made\n\n`;
        m.decisions.forEach(d => { md += `- **${d}**\n`; });
        md += `\n---\n\n`;
      }
      if (m.actionItems && m.actionItems.length > 0) {
        md += `## ⚡ Action Items & Ownership\n\n`;
        m.actionItems.forEach(a => { md += `- [ ] **${a.task}** (Owner: ${a.owner || 'Team'} | Due: ${a.deadline || 'ASAP'})\n`; });
        md += `\n---\n\n`;
      }
      md += `## 🎙️ Verbatim Master Transcript\n\n${m.masterTranscript || 'No transcript recorded.'}\n`;
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${safeTitle}_Minutes.md`;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { window.URL.revokeObjectURL(url); a.remove(); }, 1000);
      showToast(`✓ ${safeTitle}_Minutes.md downloaded!`, 'success');
      return;
    } else {
      let txt = `DISCUSSION INTELLIGENCE — MINUTES OF MEETING\nBy Elaya Narayanan\n\nTitle: ${m.title}\nDate: ${m.date} | Duration: ${Math.round((m.duration || 0)/60)} mins\nAttendees: ${m.attendees ? m.attendees.join(', ') : ''}\n\n=== EXECUTIVE SUMMARY ===\n${m.summary}\n\n`;
      if (m.decisions) {
        txt += `=== DECISIONS MADE ===\n` + m.decisions.map(d => `• ${d}`).join('\n') + '\n\n';
      }
      if (m.actionItems) {
        txt += `=== ACTION ITEMS ===\n` + m.actionItems.map(a => `[ ] ${a.task} (Owner: ${a.owner} | Due: ${a.deadline})`).join('\n') + '\n\n';
      }
      txt += `=== VERBATIM MASTER TRANSCRIPT ===\n${m.masterTranscript}\n`;
      const blob = new Blob([txt], { type: 'text/plain;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${safeTitle}_Minutes.txt`;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { window.URL.revokeObjectURL(url); a.remove(); }, 1000);
      showToast(`✓ ${safeTitle}_Minutes.txt downloaded!`, 'success');
      return;
    }
  }
  window.location.href = `/api/meetings/${meetingId}/export/${format}`;
}

function printMeetingDoc() {
  if (!selectedMeetingForModal) return;
  const m = selectedMeetingForModal;

  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    showToast('Please allow popup to generate printable report.', 'error');
    return;
  }

  const durationMin = Math.round((m.duration || 0) / 60);
  const durationText = durationMin >= 60 ? `${Math.floor(durationMin / 60)}h ${durationMin % 60}m` : `${durationMin} mins`;
  const attendeesText = m.attendees ? m.attendees.join(', ') : 'Elaya Narayanan & Strategy Team';

  const decisionsHtml = (m.decisions || []).map(d => `<li><strong>${escapeHtml(d)}</strong></li>`).join('');
  const actionItemsHtml = (m.actionItems || []).map(a => `
    <tr>
      <td style="padding: 8px; border-bottom: 1px solid #ddd;">${escapeHtml(a.task)}</td>
      <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>${escapeHtml(a.owner || 'Elaya Narayanan & Strategy Team')}</strong></td>
      <td style="padding: 8px; border-bottom: 1px solid #ddd;">${escapeHtml(a.deadline || 'ASAP')}</td>
    </tr>
  `).join('');

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>${escapeHtml(m.title)} — Minutes of Meeting</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.6; padding: 40px; max-width: 900px; margin: auto; }
        .header { border-bottom: 2px solid #0ea5e9; padding-bottom: 15px; margin-bottom: 25px; }
        .brand { font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: #0ea5e9; }
        h1 { margin: 8px 0; font-size: 24px; color: #0f172a; }
        .meta { font-size: 13px; color: #64748b; margin-top: 5px; }
        h2 { font-size: 16px; text-transform: uppercase; letter-spacing: 0.5px; color: #0369a1; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-top: 25px; }
        .summary { background: #f8fafc; border-left: 4px solid #0ea5e9; padding: 15px; font-size: 14px; border-radius: 4px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
        th { background: #f1f5f9; text-align: left; padding: 8px; border-bottom: 2px solid #cbd5e1; }
        .transcript { font-family: 'JetBrains Mono', Courier, monospace; font-size: 12px; background: #f8fafc; padding: 15px; border: 1px solid #e2e8f0; border-radius: 6px; white-space: pre-wrap; color: #334155; }
        @media print {
          body { padding: 0; }
          .no-print { display: none; }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <div class="brand">Elaya Narayanan · Discussion Intelligence & AudioSuite</div>
        <h1>${escapeHtml(m.title)}</h1>
        <div class="meta">
          <strong>Date:</strong> ${escapeHtml(m.date || '')} &nbsp;|&nbsp;
          <strong>Duration:</strong> ${durationText} &nbsp;|&nbsp;
          <strong>Category:</strong> ${escapeHtml(m.category || 'General')} &nbsp;|&nbsp;
          <strong>Attendees:</strong> ${escapeHtml(attendeesText)}
        </div>
      </div>

      <h2>📋 Executive Summary</h2>
      <div class="summary">
        ${(m.summary || 'Summary pending.').split('\n\n').map(p => `<p>${escapeHtml(p)}</p>`).join('')}
      </div>

      <h2>🎯 Key Strategic Decisions</h2>
      <ul>
        ${decisionsHtml || '<li>No explicit decisions logged.</li>'}
      </ul>

      <h2>⚡ Action Items & Accountability Matrix</h2>
      <table>
        <thead>
          <tr>
            <th>Action Item / Task</th>
            <th>Owner</th>
            <th>Deadline</th>
          </tr>
        </thead>
        <tbody>
          ${actionItemsHtml || '<tr><td colspan="3">No pending tasks.</td></tr>'}
        </tbody>
      </table>

      <h2>🎙️ Verbatim Master Transcript</h2>
      <div class="transcript">${escapeHtml(m.masterTranscript || 'No transcript available.')}</div>

      <script>
        window.onload = function() { window.print(); };
      </script>
    </body>
    </html>
  `);
  printWindow.document.close();
}

async function copyMeetingMinutes() {
  if (!selectedMeetingForModal) return;
  const m = selectedMeetingForModal;

  const durationMin = Math.round((m.duration || 0) / 60);
  const durationText = durationMin >= 60 ? `${Math.floor(durationMin / 60)}h ${durationMin % 60}m` : `${durationMin} mins`;
  const attendeesText = m.attendees ? m.attendees.join(', ') : 'Elaya Narayanan & Strategy Team';

  let text = `# ${m.title}\n\n`;
  text += `**Date:** ${m.date || ''} | **Duration:** ${durationText} | **Category:** ${m.category || 'General'}\n`;
  text += `**Attendees:** ${attendeesText}\n\n`;
  text += `## Executive Summary\n${m.summary || 'Summary pending.'}\n\n`;

  if (m.decisions && m.decisions.length > 0) {
    text += `## Strategic Decisions Made\n`;
    m.decisions.forEach(d => { text += `- ${d}\n`; });
    text += `\n`;
  }

  if (m.actionItems && m.actionItems.length > 0) {
    text += `## Action Items Matrix\n`;
    m.actionItems.forEach(a => {
      text += `- [ ] ${a.task} (Owner: ${a.owner || 'Unassigned'} | Due: ${a.deadline || 'ASAP'})\n`;
    });
    text += `\n`;
  }

  try {
    await navigator.clipboard.writeText(text);
    showToast('✓ Meeting minutes copied to clipboard in formatted Markdown!', 'success');
  } catch (err) {
    console.error('Clipboard copy failed:', err);
    showToast('Could not copy to clipboard automatically.', 'error');
  }
}

async function deleteMeeting(id) {
  if (!confirm('Are you sure you want to permanently delete this discussion session?')) return;

  try {
    const res = await fetch(`/api/meetings/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Discussion session deleted.', 'info');
      fetchMeetings();
    }
  } catch (err) {
    console.error('Failed to delete meeting:', err);
  }
}

// Instant Demo Simulation for In-Person Meeting
async function simulateMeetingDemo() {
  showToast('⚡ Simulating live discussion chunk & Gemini synthesis...', 'info');

  try {
    // Check if we need to create a meeting session first
    let targetMeetingId = activeMeetingSession ? activeMeetingSession.id : null;

    if (!targetMeetingId) {
      const title = document.getElementById('live-meeting-title').value || 'Executive Discussion Session';
      const category = document.getElementById('live-meeting-category').value || 'Product & Formulation';
      const attendees = document.getElementById('live-meeting-attendees').value.split(',').map(s => s.trim());

      const res = await fetch('/api/meetings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, category, attendees })
      });
      const data = await res.json();
      targetMeetingId = data.meeting.id;
      activeMeetingSession = { id: targetMeetingId, isRecording: true, currentSegmentIndex: 1 };
      updateRecorderControlsUI('recording');
    }

    const res2 = await fetch(`/api/meetings/${targetMeetingId}/simulate-segment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: 'Simulated 10-minute team exchange' })
    });

    const data2 = await res2.json();
    if (data2.success && data2.segment) {
      appendSegmentToLiveTranscript(data2.segment);
      if (data2.meeting) {
        updateLiveDecisionsAndActions(data2.meeting);
      }
      showToast(`✓ Simulated 10-minute segment synthesized & unified!`, 'success');
    }
  } catch (err) {
    console.error('Demo simulation error:', err);
    showToast(`Simulation error: ${err.message}`, 'error');
  }
}
