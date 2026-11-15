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

    // Process pipeline initialization
    const elBefore = document.getElementById('proc-state-before');
    if (elBefore) elBefore.innerText = '2,315 words';
    const elAction = document.getElementById('proc-action-chosen');
    if (elAction) elAction.innerText = '---';
    const elActionSub = document.getElementById('proc-action-sub');
    if (elActionSub) elActionSub.innerText = 'ready to start';
    const elClue = document.getElementById('proc-clue-code');
    if (elClue) elClue.innerText = '---';
    const elParts = document.getElementById('proc-partitions-count');
    if (elParts) elParts.innerText = '0 partitions';
    const elAfter = document.getElementById('proc-state-after');
    if (elAfter) elAfter.innerText = '2,315 words';
    const elPrunedSub = document.getElementById('proc-pruned-sub');
    if (elPrunedSub) elPrunedSub.innerText = '0 words pruned';
    const elKnown = document.getElementById('proc-known-pattern');
    if (elKnown) elKnown.innerText = 'Known: _ _ _ _ _';

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

  // Process pipeline updates (Grasp of true process)
  const elBefore = document.getElementById('proc-state-before');
  if (elBefore) elBefore.innerText = `${step.candidates_before_count.toLocaleString()} words`;
  const elAction = document.getElementById('proc-action-chosen');
  if (elAction) elAction.innerText = step.guess;
  const elActionSub = document.getElementById('proc-action-sub');
  if (elActionSub) elActionSub.innerText = step.solver_type === 'exact_dp' ? 'Optimal Bellman' : 'Heuristic move';
  const elClue = document.getElementById('proc-clue-code');
  if (elClue) elClue.innerText = step.coloring;
  const elParts = document.getElementById('proc-partitions-count');
  if (elParts) elParts.innerText = `${step.total_partitions} partitions`;
  const elAfter = document.getElementById('proc-state-after');
  if (elAfter) elAfter.innerText = `${step.candidates_after_count.toLocaleString()} words`;
  const elPrunedSub = document.getElementById('proc-pruned-sub');
  if (elPrunedSub) elPrunedSub.innerText = `-${step.eliminated_count} words (${step.reduction_pct}%)`;

  const elKnown = document.getElementById('proc-known-pattern');
  if (elKnown) {
    const knownLetters = step.known_pattern ? step.known_pattern.join(' ') : '_ _ _ _ _';
    elKnown.innerText = `Known: ${knownLetters}`;
  }

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
  const views = {
    sim: document.getElementById('view-sim'),
    comp: document.getElementById('view-comp'),
    helper: document.getElementById('view-helper')
  };
  const btns = {
    sim: document.getElementById('tab-sim-btn'),
    comp: document.getElementById('tab-comp-btn'),
    helper: document.getElementById('tab-helper-btn')
  };

  Object.keys(views).forEach(k => {
    if (views[k]) {
      if (k === tab) {
        views[k].classList.remove('hidden');
        btns[k]?.classList.remove('text-slate-400');
        btns[k]?.classList.add('bg-emerald-600', 'text-white', 'shadow');
      } else {
        views[k].classList.add('hidden');
        btns[k]?.classList.remove('bg-emerald-600', 'text-white', 'shadow');
        btns[k]?.classList.add('text-slate-400');
      }
    }
  });

  if (tab === 'comp') {
    renderCurrentComparison();
    loadBenchmarks();
  } else if (tab === 'helper') {
    if (helperHistory.length === 0) {
      fetchHelperRecommendation();
    }
  }
}

// Multi-Turn Interactive Helper State
let helperHistory = []; // Array of completed turns: [{guess: 'SALET', coloring: 'XYXXX', count: 102}, ...]
let helperCurrentTurn = 1;
let helperCurrentGuess = 'SALET';
let helperCurrentPattern = ['X', 'X', 'X', 'X', 'X'];

function resetHelperGame() {
  helperHistory = [];
  helperCurrentTurn = 1;
  helperCurrentGuess = 'SALET';
  helperCurrentPattern = ['X', 'X', 'X', 'X', 'X'];

  document.getElementById('helper-victory-card')?.classList.add('hidden');
  document.getElementById('helper-empty-card')?.classList.add('hidden');
  document.getElementById('helper-active-turn-card')?.classList.remove('hidden');
  document.getElementById('helper-undo-btn')?.classList.add('hidden');

  const guessInput = document.getElementById('helper-guess-input');
  if (guessInput) {
    guessInput.value = 'SALET';
    guessInput.disabled = false;
  }
  updateHelperTurnUI();
  updateHelperTileUI();
  fetchHelperRecommendation();
}

function undoHelperTurn() {
  if (helperHistory.length === 0) return;
  const removed = helperHistory.pop();
  helperCurrentTurn = helperHistory.length + 1;
  helperCurrentGuess = removed.guess;
  helperCurrentPattern = removed.coloring.split('');

  document.getElementById('helper-victory-card')?.classList.add('hidden');
  document.getElementById('helper-empty-card')?.classList.add('hidden');
  document.getElementById('helper-active-turn-card')?.classList.remove('hidden');

  const guessInput = document.getElementById('helper-guess-input');
  if (guessInput) {
    guessInput.value = helperCurrentGuess;
    guessInput.disabled = false;
  }

  updateHelperTurnUI();
  updateHelperTileUI();
  fetchHelperRecommendation();
}

function onHelperGuessChange() {
  const input = document.getElementById('helper-guess-input');
  if (!input) return;
  helperCurrentGuess = input.value.trim().toUpperCase();
}

function updateHelperTurnUI() {
  const badge = document.getElementById('helper-turn-badge');
  if (badge) badge.innerText = `TURN ${helperCurrentTurn} OF 6`;

  const submitText = document.getElementById('helper-submit-btn-text');
  if (submitText) submitText.innerText = `Confirm Turn ${helperCurrentTurn} & Get Next Word`;

  const undoBtn = document.getElementById('helper-undo-btn');
  if (undoBtn) {
    if (helperHistory.length > 0) undoBtn.classList.remove('hidden');
    else undoBtn.classList.add('hidden');
  }

  // Render completed history cards
  const historyContainer = document.getElementById('helper-history-list');
  if (historyContainer) {
    if (helperHistory.length === 0) {
      historyContainer.innerHTML = '';
    } else {
      let html = '';
      helperHistory.forEach((turn, idx) => {
        const colorTiles = turn.coloring.split('').map((c, i) => {
          const bg = c === 'G' ? 'bg-wordle-green' : (c === 'Y' ? 'bg-wordle-yellow' : 'bg-wordle-gray');
          const letter = turn.guess[i] || '';
          return `<span class="w-8 h-8 rounded ${bg} text-white font-bold text-sm mono flex items-center justify-center shadow-sm">${letter}</span>`;
        }).join('');

        html += `
          <div class="bg-[#141824] border border-slate-800 rounded-lg p-3.5 flex items-center justify-between shadow">
            <div class="flex items-center space-x-3">
              <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-bold text-[11px] mono">Turn ${idx + 1}</span>
              <div class="flex items-center gap-1.5">${colorTiles}</div>
              <span class="text-xs font-bold mono text-white ml-2">${turn.guess}</span>
            </div>
            <div class="flex items-center space-x-3 text-xs">
              <span class="text-slate-400 font-mono"><strong class="text-emerald-400">${turn.count}</strong> candidates remaining</span>
            </div>
          </div>
        `;
      });
      historyContainer.innerHTML = html;
    }
  }
}

function updateHelperTileUI() {
  for (let i = 0; i < 5; i++) {
    const el = document.getElementById(`helper-tile-${i}`);
    if (!el) continue;
    const ch = helperCurrentPattern[i] || 'X';
    el.innerText = ch;
    el.classList.remove('bg-wordle-gray', 'bg-wordle-yellow', 'bg-wordle-green');
    if (ch === 'G') {
      el.classList.add('bg-wordle-green');
    } else if (ch === 'Y') {
      el.classList.add('bg-wordle-yellow');
    } else {
      el.classList.add('bg-wordle-gray');
    }
  }
  const inputEl = document.getElementById('helper-pattern-input');
  if (inputEl) {
    inputEl.value = helperCurrentPattern.join('');
  }
}

function cycleHelperTile(index) {
  const nextMap = { 'X': 'Y', 'Y': 'G', 'G': 'X' };
  helperCurrentPattern[index] = nextMap[helperCurrentPattern[index]] || 'X';
  updateHelperTileUI();
}

function syncHelperPatternFromInput() {
  const inputEl = document.getElementById('helper-pattern-input');
  if (!inputEl) return;
  const raw = inputEl.value.trim().toUpperCase();
  const valid = ['G', 'Y', 'X'];
  for (let i = 0; i < 5; i++) {
    if (i < raw.length && valid.includes(raw[i])) {
      helperCurrentPattern[i] = raw[i];
    } else {
      helperCurrentPattern[i] = 'X';
    }
  }
  updateHelperTileUI();
}

function setHelperPattern(pat) {
  pat = pat.toUpperCase().slice(0, 5);
  for (let i = 0; i < 5; i++) {
    helperCurrentPattern[i] = pat[i] || 'X';
  }
  updateHelperTileUI();
}

async function submitHelperTurn() {
  const guess = (document.getElementById('helper-guess-input')?.value || helperCurrentGuess).trim().toUpperCase();
  const pattern = helperCurrentPattern.join('');

  if (guess.length !== 5) {
    alert('Please enter a valid 5-letter guess word.');
    return;
  }

  // Winning turn
  if (pattern === 'GGGGG') {
    helperHistory.push({ guess: guess, coloring: pattern, count: 1 });
    showVictoryBanner(guess, helperHistory.length);
    updateHelperTurnUI();
    return;
  }

  // Build full history parameter
  const newHistory = [...helperHistory, { guess: guess, coloring: pattern }];
  const historyParam = newHistory.map(h => `${h.guess.toLowerCase()}:${h.coloring.toUpperCase()}`).join(',');

  try {
    const res = await fetch(`/api/helper?history=${historyParam}`);
    const data = await res.json();

    // Lock in this turn
    helperHistory.push({
      guess: guess,
      coloring: pattern,
      count: data.candidates_count
    });

    helperCurrentTurn = helperHistory.length + 1;

    // Check outcome
    if (data.status === 'solved' || data.candidates_count === 1) {
      showVictoryBanner(data.recommended_guess, helperHistory.length);
    } else if (data.status === 'empty' || data.candidates_count === 0) {
      document.getElementById('helper-empty-card')?.classList.remove('hidden');
      document.getElementById('helper-active-turn-card')?.classList.add('hidden');
    } else {
      helperCurrentGuess = data.recommended_guess || 'SALET';
      const guessInput = document.getElementById('helper-guess-input');
      if (guessInput) {
        guessInput.value = helperCurrentGuess;
      }
      helperCurrentPattern = ['X', 'X', 'X', 'X', 'X'];
      updateHelperTileUI();
    }

    updateHelperTurnUI();
    renderHelperDiagnostics(data);
  } catch (e) {
    console.error('Error submitting helper turn:', e);
  }
}

async function fetchHelperRecommendation() {
  const historyParam = helperHistory.map(h => `${h.guess.toLowerCase()}:${h.coloring.toUpperCase()}`).join(',');
  const url = historyParam ? `/api/helper?history=${historyParam}` : `/api/helper?history=salet:xxxxx`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (helperHistory.length === 0) {
      data.recommended_guess = 'SALET';
      data.candidates_count = 2315;
      data.reason = 'Optimal opening word proven by MIT paper (Avg 3.42 guesses)';
    }
    renderHelperDiagnostics(data);
  } catch (e) {
    console.error('Error fetching helper recommendation:', e);
  }
}

function showVictoryBanner(word, turns) {
  const victoryCard = document.getElementById('helper-victory-card');
  const victoryMsg = document.getElementById('helper-victory-msg');
  const activeTurnCard = document.getElementById('helper-active-turn-card');

  if (victoryCard) victoryCard.classList.remove('hidden');
  if (activeTurnCard) activeTurnCard.classList.add('hidden');
  if (victoryMsg) {
    victoryMsg.innerHTML = `The hidden word is <strong class="text-white text-base mono font-black">${word}</strong>! Solved in <strong class="text-emerald-400 font-bold">${turns} moves</strong> with 100% certainty.`;
  }

  const recWordEl = document.getElementById('helper-rec-word');
  if (recWordEl) recWordEl.innerText = word;
  const countEl = document.getElementById('helper-candidates-count');
  if (countEl) countEl.innerText = '1';
  const pctEl = document.getElementById('helper-search-space-pct');
  if (pctEl) pctEl.innerText = '0.04%';
}

function renderHelperDiagnostics(data) {
  if (!data) return;

  const recWordEl = document.getElementById('helper-rec-word');
  const recReasonEl = document.getElementById('helper-rec-reason');
  const countEl = document.getElementById('helper-candidates-count');
  const badgeEl = document.getElementById('helper-candidates-badge');
  const cloudEl = document.getElementById('helper-candidates-cloud');
  const pctEl = document.getElementById('helper-search-space-pct');
  const pathContainer = document.getElementById('helper-tree-path-container');

  if (recWordEl) recWordEl.innerText = data.recommended_guess || '---';
  if (recReasonEl) recReasonEl.innerText = data.reason || 'Optimal Move';
  if (countEl) countEl.innerText = data.candidates_count;
  if (badgeEl) badgeEl.innerText = `${data.candidates_count} words`;

  if (pctEl) {
    const pct = ((data.candidates_count / 2315) * 100).toFixed(1);
    pctEl.innerText = `${pct}%`;
  }

  // Candidates Cloud
  if (cloudEl) {
    if (!data.candidates_sample || data.candidates_sample.length === 0) {
      cloudEl.innerHTML = '<span class="text-xs text-rose-400">No matching words remaining</span>';
    } else {
      cloudEl.innerHTML = data.candidates_sample.map(w => `
        <span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 text-xs font-mono font-medium hover:border-emerald-500 hover:text-white transition">
          ${w.toUpperCase()}
        </span>
      `).join('');
      if (data.candidates_count > data.candidates_sample.length) {
        cloudEl.innerHTML += `<span class="text-xs text-slate-500 italic self-center ml-1">+${data.candidates_count - data.candidates_sample.length} more</span>`;
      }
    }
  }

  // Path Trace
  if (pathContainer && data.path) {
    let html = '';
    data.path.forEach(node => {
      if (node.is_leaf) {
        html += `
          <div class="flex items-center space-x-2.5 p-2 bg-emerald-950/30 border border-emerald-500/40 rounded-lg text-xs">
            <i class="fa-solid fa-check text-emerald-400"></i>
            <div>
              <span class="text-[10px] uppercase text-emerald-400 font-bold">Recommended Guess:</span>
              <span class="font-black mono text-white ml-1">${node.recommended_guess}</span>
            </div>
          </div>
        `;
      } else {
        html += `
          <div class="flex items-center justify-between p-1.5 bg-slate-900/60 border border-slate-800 rounded text-xs">
            <span class="text-slate-300 text-[11px]">${node.question}</span>
            <span class="px-1.5 py-0.5 text-[9px] rounded bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30">MATCH</span>
          </div>
        `;
      }
    });
    pathContainer.innerHTML = html;
  }
}

// Startup
window.addEventListener('DOMContentLoaded', () => {
  initBoard();
  initAlphabetTracker();
  fetchSimulation();
});
