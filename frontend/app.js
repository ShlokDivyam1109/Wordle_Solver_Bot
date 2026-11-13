// State Management
let currentSecret = 'CIGAR';
let currentSteps = [];
let currentComparison = null;
let currentStepIndex = 0;
let isPlaying = false;
let playTimer = null;
let animSpeed = 900;
let benchmarkData = null;

// Alphabet list
const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

// Initialize 6x5 Wordle Board
function initBoard() {
  const boardEl = document.getElementById('board');
  if (!boardEl) return;
  boardEl.innerHTML = '';
  for (let r = 0; r < 6; r++) {
    const row = document.createElement('div');
    row.id = `row-${r}`;
    row.className = 'grid grid-cols-5 gap-2 w-full h-12';
    for (let c = 0; c < 5; c++) {
      const tile = document.createElement('div');
      tile.id = `tile-${r}-${c}`;
      tile.className = 'wordle-tile w-full h-full';
      tile.innerHTML = `
        <div class="tile-inner">
          <div class="tile-front font-bold text-lg mono"></div>
          <div class="tile-back font-bold text-lg mono"></div>
        </div>
      `;
      row.appendChild(tile);
    }
    boardEl.appendChild(row);
  }
}

// Initialize Alphabet Tracker Keyboard
function initAlphabetTracker() {
  const container = document.getElementById('alphabet-tracker');
  if (!container) return;
  container.innerHTML = '';
  ALPHABET.forEach(letter => {
    const key = document.createElement('div');
    key.id = `key-${letter}`;
    key.className = 'key-tile key-untested';
    key.innerText = letter;
    container.appendChild(key);
  });
}

// Update Alphabet Tracker State
function updateAlphabetTracker(alphabetState) {
  ALPHABET.forEach(letter => {
    const key = document.getElementById(`key-${letter}`);
    if (!key) return;
    key.className = 'key-tile';
    const st = alphabetState ? alphabetState[letter] : 'untested';
    if (st === 'green') {
      key.classList.add('key-green');
    } else if (st === 'yellow') {
      key.classList.add('key-yellow');
    } else if (st === 'eliminated') {
      key.classList.add('key-eliminated');
    } else {
      key.classList.add('key-untested');
    }
  });
}

// Step-by-Step 3D Tile Flip Reveal
function revealRowStepByStep(rowIndex, tileStates, callback) {
  const row = document.getElementById(`row-${rowIndex}`);
  if (!row) return;

  tileStates.forEach((ts, colIndex) => {
    setTimeout(() => {
      const tile = document.getElementById(`tile-${rowIndex}-${colIndex}`);
      if (!tile) return;
      const front = tile.querySelector('.tile-front');
      const back = tile.querySelector('.tile-back');

      front.innerText = ts.letter;
      back.innerText = ts.letter;

      back.classList.remove('bg-wordle-green', 'bg-wordle-yellow', 'bg-wordle-gray');
      if (ts.state === 'green') {
        back.classList.add('bg-wordle-green');
      } else if (ts.state === 'yellow') {
        back.classList.add('bg-wordle-yellow');
      } else {
        back.classList.add('bg-wordle-gray');
      }

      tile.classList.add('tile-flipped');

      if (colIndex === 4 && callback) {
        setTimeout(callback, 200);
      }
    }, colIndex * 180);
  });
}

// Instantly Render Row (No Delay for Fast Scrubbing)
function setRowInstant(rowIndex, tileStates) {
  const row = document.getElementById(`row-${rowIndex}`);
  if (!row) return;

  tileStates.forEach((ts, colIndex) => {
    const tile = document.getElementById(`tile-${rowIndex}-${colIndex}`);
    if (!tile) return;
    const front = tile.querySelector('.tile-front');
    const back = tile.querySelector('.tile-back');

    front.innerText = ts.letter;
    back.innerText = ts.letter;

    back.classList.remove('bg-wordle-green', 'bg-wordle-yellow', 'bg-wordle-gray');
    if (ts.state === 'green') {
      back.classList.add('bg-wordle-green');
    } else if (ts.state === 'yellow') {
      back.classList.add('bg-wordle-yellow');
    } else {
      back.classList.add('bg-wordle-gray');
    }

    tile.classList.add('tile-flipped');
  });
}

function clearRow(rowIndex) {
  const row = document.getElementById(`row-${rowIndex}`);
  if (!row) return;
  row.classList.remove('win-row');
  for (let c = 0; c < 5; c++) {
    const tile = document.getElementById(`tile-${rowIndex}-${c}`);
    if (!tile) continue;
    tile.classList.remove('tile-flipped');
    const front = tile.querySelector('.tile-front');
    const back = tile.querySelector('.tile-back');
    front.innerText = '';
    back.innerText = '';
    back.classList.remove('bg-wordle-green', 'bg-wordle-yellow', 'bg-wordle-gray');
  }
}

// Update UI Diagnostics & Backend Inspector
function updateDiagnostics() {
  const stepCount = currentSteps.length;
  document.getElementById('step-indicator').innerText = `Step ${currentStepIndex} / ${stepCount}`;

  if (currentStepIndex === 0) {
    document.getElementById('stat-candidates').innerText = '2,315';
    document.getElementById('stat-eliminated').innerText = '0';
    document.getElementById('stat-entropy').innerText = '0.00';
    document.getElementById('stat-value').innerText = '3.42';
    document.getElementById('reduction-pct-badge').innerText = '0% Pruned';
    document.getElementById('space-collapse-bar').style.width = '0%';
    document.getElementById('backend-reason-text').innerText = 'Simulation initialized with full 2,315-word vocabulary. Ready to execute first guess.';
    document.getElementById('step-clue-container').innerHTML = '';
    document.getElementById('candidate-count-badge').innerText = '2,315 words';
    document.getElementById('win-badge').classList.add('hidden');
    updateAlphabetTracker(null);

    // Initial partition message
    const partContainer = document.getElementById('partitions-container');
    if (partContainer) {
      partContainer.innerHTML = '<div class="text-xs text-slate-500 text-center py-4">Execute a guess to inspect partitions.</div>';
    }

    // Initial words sample
    const cloud = document.getElementById('candidate-cloud');
    if (cloud && currentSteps.length > 0 && currentSteps[0].candidates_sample) {
      let sample = ['cigar', 'rebut', 'sissy', 'humph', 'awake', 'blush', 'focal', 'evade', 'naval', 'serve', 'heath', 'dwarf', 'model', 'karma', 'stink', 'grade', 'quiet', 'bench', 'abate', 'feign'];
      cloud.innerHTML = sample.map(w => `<span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">${w}</span>`).join('');
    }
    return;
  }

  const step = currentSteps[currentStepIndex - 1];
  if (!step) return;

  // Numerical metrics
  document.getElementById('stat-candidates').innerText = step.candidates_after_count.toLocaleString();
  document.getElementById('stat-eliminated').innerText = step.eliminated_count.toLocaleString();
  document.getElementById('stat-entropy').innerText = step.entropy_bits.toFixed(2);
  document.getElementById('stat-value').innerText = step.expected_cost.toFixed(2);

  // Search space reduction bar
  const totalPrunedPct = Math.min(100, Math.round(((2315 - step.candidates_after_count) / 2315) * 100));
  document.getElementById('reduction-pct-badge').innerText = `${totalPrunedPct}% Pruned (${step.reduction_pct}% this turn)`;
  document.getElementById('space-collapse-bar').style.width = `${totalPrunedPct}%`;

  // Backend algorithmic reasoning text
  document.getElementById('backend-reason-text').innerText = step.backend_reason;

  // Feedback clue badge tiles
  let clueHtml = '';
  step.tile_states.forEach(ts => {
    let bgClass = ts.state === 'green' ? 'bg-wordle-green text-white' : (ts.state === 'yellow' ? 'bg-wordle-yellow text-white' : 'bg-wordle-gray text-slate-300');
    clueHtml += `<span class="w-6 h-6 rounded flex items-center justify-center font-bold text-xs ${bgClass} shadow-sm">${ts.letter}</span>`;
  });
  document.getElementById('step-clue-container').innerHTML = clueHtml;

  // Alphabet deduction keyboard
  updateAlphabetTracker(step.alphabet_state);

  // Surviving Candidates Word Cloud
  const cloud = document.getElementById('candidate-cloud');
  const countBadge = document.getElementById('candidate-count-badge');
  if (cloud && countBadge) {
    countBadge.innerText = `${step.candidates_after_count.toLocaleString()} words`;
    if (step.candidates_after_count === 1) {
      cloud.innerHTML = `<span class="px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono font-bold text-xs">Sole Solution: ${step.candidates_sample[0].toUpperCase()}</span>`;
    } else {
      let words = step.candidates_sample || [];
      cloud.innerHTML = words.map(w => `<span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">${w}</span>`).join('');
    }
  }

  // Active Partitions Breakdown
  const partContainer = document.getElementById('partitions-container');
  if (partContainer) {
    if (step.top_partitions && step.top_partitions.length > 0) {
      let maxCount = step.top_partitions[0].count;
      let partHtml = '';
      step.top_partitions.forEach(p => {
        let isMatchingBucket = (p.coloring === step.coloring);
        let pct = Math.max(8, Math.round((p.count / maxCount) * 100));
        let barColor = isMatchingBucket ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-300';
        partHtml += `
          <div class="flex items-center space-x-2 text-[11px]">
            <span class="w-14 font-mono font-bold text-center py-0.5 rounded ${isMatchingBucket ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-900 text-slate-400'}">${p.coloring}</span>
            <div class="flex-1 bg-slate-900 rounded h-4 overflow-hidden p-0.5">
              <div class="${barColor} h-full rounded text-[10px] flex items-center justify-end px-1.5 font-mono font-semibold" style="width: ${pct}%">
                ${p.count}
              </div>
            </div>
            ${isMatchingBucket ? '<span class="text-[10px] text-emerald-400 font-bold">Active</span>' : ''}
          </div>
        `;
      });
      partContainer.innerHTML = partHtml;
    } else {
      partContainer.innerHTML = '<div class="text-xs text-slate-500 text-center py-4">No remaining partitions.</div>';
    }
  }

  // Win Badge
  if (step.is_won) {
    const winBadge = document.getElementById('win-badge');
    const winTurn = document.getElementById('win-turn');
    if (winBadge && winTurn) {
      winTurn.innerText = step.step_index;
      winBadge.classList.remove('hidden');
    }
    const winRow = document.getElementById(`row-${step.step_index - 1}`);
    if (winRow) winRow.classList.add('win-row');
  } else {
    document.getElementById('win-badge').classList.add('hidden');
  }
}

// Navigation Controls
function nextStep() {
  if (currentStepIndex >= currentSteps.length) {
    pausePlay();
    return;
  }
  const nextIdx = currentStepIndex;
  const step = currentSteps[nextIdx];
  currentStepIndex++;
  revealRowStepByStep(nextIdx, step.tile_states, () => {
    updateDiagnostics();
  });
}

function prevStep() {
  if (currentStepIndex <= 0) return;
  pausePlay();
  currentStepIndex--;
  clearRow(currentStepIndex);
  updateDiagnostics();
}

function resetPlayback() {
  pausePlay();
  currentStepIndex = 0;
  for (let r = 0; r < 6; r++) clearRow(r);
  updateDiagnostics();
}

function togglePlay() {
  if (isPlaying) {
    pausePlay();
  } else {
    startPlay();
  }
}

function startPlay() {
  if (currentStepIndex >= currentSteps.length) {
    resetPlayback();
  }
  isPlaying = true;
  document.getElementById('play-icon').classList.remove('fa-play');
  document.getElementById('play-icon').classList.add('fa-pause');

  playTimer = setInterval(() => {
    if (currentStepIndex < currentSteps.length) {
      nextStep();
    } else {
      pausePlay();
    }
  }, animSpeed);
}

function pausePlay() {
  isPlaying = false;
  if (playTimer) clearInterval(playTimer);
  document.getElementById('play-icon').classList.remove('fa-pause');
  document.getElementById('play-icon').classList.add('fa-play');
}

function setSpeed(ms, btn) {
  animSpeed = ms;
  document.querySelectorAll('.speed-btn').forEach(b => {
    b.classList.remove('bg-emerald-600', 'text-white', 'font-bold');
    b.classList.add('bg-slate-800', 'text-slate-300');
  });
  btn.classList.remove('bg-slate-800', 'text-slate-300');
  btn.classList.add('bg-emerald-600', 'text-white', 'font-bold');

  if (isPlaying) {
    pausePlay();
    startPlay();
  }
}

// Words Helpers
function setWord(w) {
  document.getElementById('target-word-input').value = w.toUpperCase();
  applyCustomWord();
}

function applyCustomWord() {
  const val = document.getElementById('target-word-input').value.trim().toLowerCase();
  if (val.length === 5) {
    currentSecret = val;
    fetchSimulation();
  }
}

async function pickRandomWord() {
  try {
    const res = await fetch('/api/random');
    const data = await res.json();
    document.getElementById('target-word-input').value = data.word.toUpperCase();
    currentSecret = data.word.toLowerCase();
    fetchSimulation();
  } catch (e) {
    console.error(e);
  }
}

// Fetch Simulation & Multi-Solver Comparison from Backend
async function fetchSimulation() {
  pausePlay();
  const solver = document.getElementById('solver-select').value;
  try {
    const res = await fetch(`/api/simulate?secret=${currentSecret}&solver=${solver}`);
    const data = await res.json();
    currentSteps = data.steps || [];
    currentComparison = data.comparison || null;

    // Update Comparison page dynamically
    renderCurrentComparison();

    resetPlayback();
  } catch (e) {
    console.error('Error fetching simulation:', e);
  }
}

// Render Live Current Word Multi-Solver Comparison
function renderCurrentComparison() {
  if (!currentComparison) return;

  const secretEl = document.getElementById('comp-current-secret');
  if (secretEl) secretEl.innerText = currentComparison.secret;

  const winnerEl = document.getElementById('comp-winner-name');
  if (winnerEl) {
    winnerEl.innerText = `${currentComparison.winner} (${currentComparison.best_guesses} guesses)`;
  }

  const tbody = document.getElementById('comp-current-tbody');
  if (!tbody || !currentComparison.solvers) return;

  let html = '';
  currentComparison.solvers.forEach((s, idx) => {
    const isWinner = (s.guesses === currentComparison.best_guesses && s.won);
    const rowClass = isWinner ? 'bg-emerald-950/25 text-white font-semibold' : 'text-slate-300';
    
    // Path pills
    let pathHtml = '';
    s.path.forEach((w, pIdx) => {
      let isLast = pIdx === s.path.length - 1;
      let badgeColor = isLast && s.won ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-300';
      pathHtml += `<span class="px-1.5 py-0.5 rounded text-[11px] font-mono ${badgeColor}">${w}</span>`;
      if (!isLast) pathHtml += '<i class="fa-solid fa-arrow-right text-[9px] text-slate-600 mx-1"></i>';
    });

    html += `
      <tr class="${rowClass}">
        <td class="py-3 px-4">
          <div class="flex items-center space-x-2">
            ${isWinner ? '<i class="fa-solid fa-trophy text-amber-400 text-xs"></i>' : ''}
            <span class="${isWinner ? 'text-emerald-400 font-bold' : 'text-slate-200'}">${s.name}</span>
          </div>
          <span class="text-[10px] text-slate-500 font-sans">${s.tag}</span>
        </td>
        <td class="py-3 px-4 font-mono font-bold">${s.first_guess}</td>
        <td class="py-3 px-4 font-mono text-base font-bold ${isWinner ? 'text-emerald-400' : 'text-slate-200'}">
          ${s.guesses}
        </td>
        <td class="py-3 px-4">
          <div class="flex flex-wrap items-center gap-y-1">
            ${pathHtml}
          </div>
        </td>
        <td class="py-3 px-4">
          ${s.won ? 
            '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">WON</span>' : 
            '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">FAILED</span>'}
        </td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

// Load Benchmark Data for Literature Comparison
async function loadBenchmarks() {
  try {
    if (!benchmarkData) {
      const res = await fetch('/api/benchmarks');
      benchmarkData = await res.json();
    }

    const tbody = document.getElementById('benchmark-tbody');
    if (!tbody || !benchmarkData) return;

    const solvers = [
      { key: 'exact_dp', certified: true, tradeoff: 'Global Bellman Optimum; 100% win rate' },
      { key: 'two_step_greedy', certified: false, tradeoff: 'Truncated 2-step horizon; blind to deep traps' },
      { key: 'entropy_greedy', certified: false, tradeoff: 'Greedy 1-step myopic; ignores multi-turn branch size' },
      { key: 'max_partitions', certified: false, tradeoff: 'Maximizes bin count; ignores bin size variance' },
      { key: 'random', certified: false, tradeoff: 'No strategic information discovery' }
    ];

    let html = '';
    solvers.forEach(s => {
      const item = benchmarkData[s.key];
      if (!item) return;
      const isOptimal = s.key === 'exact_dp';

      html += `
        <tr class="${isOptimal ? 'bg-emerald-950/20 text-white font-semibold' : 'text-slate-300'}">
          <td class="py-3 px-4 ${isOptimal ? 'text-emerald-400 font-bold' : ''}">${item.name}</td>
          <td class="py-3 px-4 mono font-bold">${item.first_guess}</td>
          <td class="py-3 px-4 mono font-bold text-white">${item.avg_guesses.toFixed(3)}</td>
          <td class="py-3 px-4 mono">${item.max_guesses}</td>
          <td class="py-3 px-4 mono ${item.win_rate >= 100 ? 'text-emerald-400 font-bold' : 'text-amber-400'}">${item.win_rate.toFixed(1)}%</td>
          <td class="py-3 px-4">
            ${s.certified ? 
              '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Certifiably Optimal</span>' : 
              '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-400">Heuristic</span>'}
          </td>
          <td class="py-3 px-4 text-xs font-sans text-slate-400">${s.tradeoff}</td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  } catch (e) {
    console.error('Error loading benchmarks:', e);
  }
}

// Tab Switching
function switchTab(tab) {
  const simView = document.getElementById('view-sim');
  const compView = document.getElementById('view-comp');
  const simBtn = document.getElementById('tab-sim-btn');
  const compBtn = document.getElementById('tab-comp-btn');

  if (tab === 'sim') {
    simView.classList.remove('hidden');
    compView.classList.add('hidden');
    simBtn.classList.remove('text-slate-400');
    simBtn.classList.add('bg-emerald-600', 'text-white', 'shadow');
    compBtn.classList.remove('bg-emerald-600', 'text-white', 'shadow');
    compBtn.classList.add('text-slate-400');
  } else {
    simView.classList.add('hidden');
    compView.classList.remove('hidden');
    compBtn.classList.remove('text-slate-400');
    compBtn.classList.add('bg-emerald-600', 'text-white', 'shadow');
    simBtn.classList.remove('bg-emerald-600', 'text-white', 'shadow');
    simBtn.classList.add('text-slate-400');

    renderCurrentComparison();
    loadBenchmarks();
  }
}

// Startup
window.addEventListener('DOMContentLoaded', () => {
  initBoard();
  initAlphabetTracker();
  fetchSimulation();
});
