"""
Interactive Wordle Solver Animated Web Dashboard.
Implementation of Bertsimas & Paskov (MIT) - 'An Exact and Interpretable Solution to Wordle'.

Run with:
    python web_app.py
Then open http://localhost:8080 in your browser.
"""

import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import engine
import tree

PORT = 8080
solver_instance = engine.WordleSolver()
tree_policy = tree.InterpretableTreePolicy()
tree_policy.train_on_salet_g2()

BENCHMARK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'benchmark_results.json')
benchmark_cache = None
if os.path.exists(BENCHMARK_PATH):
    try:
        with open(BENCHMARK_PATH, 'r', encoding='utf-8') as f:
            benchmark_cache = json.load(f)
    except Exception:
        pass


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Exact & Interpretable Wordle Solver — MIT DP Framework</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    
    body {
      font-family: 'Inter', sans-serif;
      background-color: #0f1117;
      color: #e2e8f0;
    }
    .mono {
      font-family: 'JetBrains Mono', monospace;
    }
    
    /* Authentic Wordle 3D Flip Animation */
    .wordle-tile {
      perspective: 1000px;
      transition: all 0.25s ease;
    }
    .tile-inner {
      position: relative;
      width: 100%;
      height: 100%;
      text-align: center;
      transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
      transform-style: preserve-3d;
    }
    .tile-flipped .tile-inner {
      transform: rotateX(180deg);
    }
    .tile-front, .tile-back {
      position: absolute;
      width: 100%;
      height: 100%;
      backface-visibility: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
    }
    .tile-front {
      background-color: #1e2230;
      border: 2px solid #333a4d;
      color: #f8fafc;
    }
    .tile-back {
      transform: rotateX(180deg);
      border: 2px solid transparent;
      color: #ffffff;
      font-weight: 800;
    }
    
    /* Wordle Official Tile Colors */
    .bg-wordle-green { background-color: #538d4e !important; }
    .bg-wordle-yellow { background-color: #b59f3b !important; }
    .bg-wordle-gray { background-color: #3a3a3c !important; }
    .border-wordle-green { border-color: #538d4e !important; }
    
    /* Pulse for victory */
    @keyframes winPulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.04); }
    }
    .win-row {
      animation: winPulse 0.8s ease-in-out infinite alternate;
    }

    /* Custom scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #1a1e2e; }
    ::-webkit-scrollbar-thumb { background: #3b4261; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #565f89; }
  </style>
</head>
<body class="min-h-screen flex flex-col">

  <!-- Header -->
  <header class="border-b border-slate-800 bg-[#141824]/90 backdrop-blur sticky top-0 z-50 px-6 py-4">
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-black text-xl mono">
          W
        </div>
        <div>
          <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            Exact & Interpretable Wordle Solver
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">MIT DP Framework</span>
          </h1>
          <p class="text-xs text-slate-400">Bertsimas & Paskov — Certifiably Optimal Bellman Recursion with OCT-H Interpretability</p>
        </div>
      </div>

      <!-- Quick Nav Tabs -->
      <div class="flex items-center space-x-2 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
        <button id="tab-play-btn" onclick="switchTab('play')" class="px-3 py-1.5 rounded-md text-xs font-medium transition bg-emerald-600 text-white shadow-sm flex items-center gap-1.5">
          <i class="fa-solid fa-gamepad"></i> Solver Playback
        </button>
        <button id="tab-tree-btn" onclick="switchTab('tree')" class="px-3 py-1.5 rounded-md text-xs font-medium transition text-slate-400 hover:text-white flex items-center gap-1.5">
          <i class="fa-solid fa-network-wired"></i> OCT-H Tree
        </button>
        <button id="tab-metrics-btn" onclick="switchTab('metrics')" class="px-3 py-1.5 rounded-md text-xs font-medium transition text-slate-400 hover:text-white flex items-center gap-1.5">
          <i class="fa-solid fa-chart-line"></i> Benchmark & Metrics
        </button>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">

    <!-- VIEW 1: GAME PLAYBACK -->
    <div id="view-play" class="space-y-6">
      <!-- Controls Topbar -->
      <div class="bg-[#141824] border border-slate-800 rounded-xl p-4 shadow-lg flex flex-wrap items-center justify-between gap-4">
        
        <!-- Target Word Selection -->
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center space-x-2">
            <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Hidden Word:</label>
            <div class="relative">
              <input id="target-word-input" type="text" maxlength="5" value="VIXEN" 
                     class="w-28 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-sm font-bold text-center tracking-widest uppercase text-emerald-400 focus:outline-none focus:border-emerald-500 mono"
                     onkeyup="if(event.key==='Enter') applyCustomWord()">
              <button onclick="applyCustomWord()" class="absolute right-1 top-1.5 text-slate-400 hover:text-white px-1.5 text-xs">
                <i class="fa-solid fa-arrow-right"></i>
              </button>
            </div>
          </div>

          <button onclick="pickRandomWord()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium text-slate-300 transition flex items-center gap-1.5">
            <i class="fa-solid fa-shuffle text-emerald-400"></i> Random Word
          </button>

          <!-- Presets from Paper -->
          <div class="flex items-center space-x-1 pl-2 border-l border-slate-800">
            <span class="text-xs text-slate-500 mr-1">Paper Presets:</span>
            <button onclick="setWord('LIGHT')" class="px-2 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded text-xs font-mono font-bold" title="Figure 6: LIGHT trap solved by FERMS">LIGHT (Trap)</button>
            <button onclick="setWord('VIXEN')" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-mono font-bold" title="Figure 1: Repeated E + V, N">VIXEN</button>
            <button onclick="setWord('JIFFY')" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-mono font-bold" title="Figure 7: Info-starved recovery">JIFFY</button>
            <button onclick="setWord('FOCAL')" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-mono font-bold">FOCAL</button>
          </div>
        </div>

        <!-- Solver Selector -->
        <div class="flex items-center space-x-3">
          <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Algorithm:</label>
          <select id="solver-select" onchange="fetchSimulation()" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-medium text-white focus:outline-none focus:border-emerald-500">
            <option value="exact_dp" selected>Exact DP (Optimal - SALET)</option>
            <option value="entropy">Shannon Entropy Greedy (SOARE)</option>
            <option value="two_step">2-Step Lookahead (WordleBot - CRANE)</option>
            <option value="max_partitions">Max Partitions Greedy (TRACE)</option>
            <option value="random">Random Candidate Selection</option>
          </select>
        </div>
      </div>

      <!-- Main Layout: Board (Left) + Solver Diagnostics & Candidate Cloud (Right) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

        <!-- Left: Wordle Board & Animation Controls (5 cols) -->
        <div class="lg:col-span-5 space-y-4">
          <div class="bg-[#141824] border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col items-center justify-center">
            
            <!-- 6x5 Wordle Board -->
            <div id="board" class="grid grid-rows-6 gap-2 w-72 h-84 mb-6">
              <!-- Rendered via JS -->
            </div>

            <!-- Playback Controls -->
            <div class="w-full bg-slate-900/90 rounded-xl p-3 border border-slate-800 space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-xs font-medium text-slate-400" id="step-indicator">Step 0 / 0</span>
                <span id="win-badge" class="hidden px-2 py-0.5 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                  <i class="fa-solid fa-trophy mr-1"></i> Solved in <span id="win-turn">4</span> guesses
                </span>
              </div>

              <div class="flex items-center justify-center space-x-3">
                <button onclick="prevStep()" class="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition" title="Previous Step">
                  <i class="fa-solid fa-backward-step"></i>
                </button>
                <button id="play-pause-btn" onclick="togglePlay()" class="w-12 h-12 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center text-lg shadow-lg shadow-emerald-900/30 transition" title="Play / Pause Animation">
                  <i id="play-icon" class="fa-solid fa-play"></i>
                </button>
                <button onclick="nextStep()" class="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition" title="Next Step">
                  <i class="fa-solid fa-forward-step"></i>
                </button>
                <button onclick="resetPlayback()" class="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition" title="Reset">
                  <i class="fa-solid fa-rotate-left"></i>
                </button>
              </div>

              <!-- Speed Controls -->
              <div class="flex items-center justify-between pt-2 border-t border-slate-800 text-xs text-slate-400">
                <span>Speed:</span>
                <div class="flex items-center space-x-1">
                  <button onclick="setSpeed(1500, this)" class="speed-btn px-2 py-0.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700">0.5x</button>
                  <button onclick="setSpeed(900, this)" class="speed-btn px-2 py-0.5 rounded bg-emerald-600 text-white font-bold">1x</button>
                  <button onclick="setSpeed(450, this)" class="speed-btn px-2 py-0.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700">2x</button>
                </div>
              </div>
            </div>

          </div>

          <!-- Solver Guarantee Badge -->
          <div class="bg-gradient-to-r from-emerald-950/40 to-slate-900 border border-emerald-500/30 rounded-xl p-4 flex items-center space-x-3">
            <div class="w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 text-lg">
              <i class="fa-solid fa-certificate"></i>
            </div>
            <div>
              <div class="text-xs font-bold text-emerald-400 uppercase tracking-wide">Certifiably Optimal Guarantee</div>
              <div class="text-xs text-slate-300">Exact DP guarantees finding all 2,315 hidden words in &le; 5 guesses (100% win rate).</div>
            </div>
          </div>
        </div>

        <!-- Right: Real-Time Diagnostic Panels (7 cols) -->
        <div class="lg:col-span-7 space-y-6">

          <!-- Current Step Metrics Card -->
          <div class="bg-[#141824] border border-slate-800 rounded-xl p-5 shadow-lg">
            <div class="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <i class="fa-solid fa-microchip text-emerald-400"></i> Step Diagnostics
              </h2>
              <span id="current-guess-pill" class="text-xs font-mono font-bold px-2 py-1 rounded bg-slate-800 text-slate-300">
                Waiting to begin...
              </span>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <div class="text-[10px] uppercase font-bold text-slate-500">Candidates Left</div>
                <div id="stat-candidates" class="text-xl font-bold text-white mono mt-1">2,315</div>
                <div id="stat-eliminated" class="text-[10px] text-slate-400 mt-0.5">0 eliminated</div>
              </div>
              <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <div class="text-[10px] uppercase font-bold text-slate-500">Reduction</div>
                <div id="stat-reduction" class="text-xl font-bold text-emerald-400 mono mt-1">0%</div>
                <div class="text-[10px] text-slate-400 mt-0.5">search space pruned</div>
              </div>
              <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <div class="text-[10px] uppercase font-bold text-slate-500">Info Gained</div>
                <div id="stat-entropy" class="text-xl font-bold text-indigo-400 mono mt-1">0.00</div>
                <div class="text-[10px] text-slate-400 mt-0.5">Shannon bits</div>
              </div>
              <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <div class="text-[10px] uppercase font-bold text-slate-500">Expected Guesses</div>
                <div id="stat-value" class="text-xl font-bold text-amber-400 mono mt-1">3.42</div>
                <div class="text-[10px] text-slate-400 mt-0.5">Bellman value V*</div>
              </div>
            </div>
          </div>

          <!-- Partition Distribution Breakdown -->
          <div class="bg-[#141824] border border-slate-800 rounded-xl p-5 shadow-lg">
            <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <span class="flex items-center gap-2">
                <i class="fa-solid fa-chart-simple text-indigo-400"></i> Coloring Partitions Produced by Guess
              </span>
              <span class="text-xs text-slate-400 font-normal">How the guess splits candidate words</span>
            </h2>
            <div id="partitions-container" class="space-y-2">
              <div class="text-xs text-slate-500 text-center py-4">Make a guess to view how it partitions candidates.</div>
            </div>
          </div>

          <!-- Candidate Word Cloud (Shrinking in Real-Time) -->
          <div class="bg-[#141824] border border-slate-800 rounded-xl p-5 shadow-lg">
            <div class="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <i class="fa-solid fa-list-check text-emerald-400"></i> Remaining Viable Candidates
              </h2>
              <span id="candidate-count-badge" class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                2,315 words
              </span>
            </div>
            
            <div id="candidate-cloud" class="flex flex-wrap gap-1.5 max-h-44 overflow-y-auto p-2 bg-slate-900/60 rounded-lg border border-slate-800/80">
              <!-- Rendered via JS -->
            </div>
          </div>

        </div>

      </div>
    </div>

    <!-- VIEW 2: OCT-H DECISION TREE -->
    <div id="view-tree" class="hidden space-y-6">
      <div class="bg-[#141824] border border-slate-800 rounded-xl p-6 shadow-xl">
        <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <i class="fa-solid fa-network-wired text-emerald-400"></i> Optimal Classification Tree with Hyperplanes (OCT-H)
            </h2>
            <p class="text-xs text-slate-400">Section 2.3 & 2.4 — 15n binary tile features mapped to optimal next actions</p>
          </div>

          <div class="flex items-center space-x-2">
            <span class="text-xs text-slate-400">Coloring Pattern for Guess 1 (SALET):</span>
            <input id="tree-coloring-input" type="text" maxlength="5" value="XXXXX" 
                   class="w-24 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs font-mono font-bold uppercase text-center text-emerald-400"
                   onchange="traceTreePath()">
            <button onclick="traceTreePath()" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium">Trace Path</button>
          </div>
        </div>

        <!-- Tree Path Breadcrumbs -->
        <div class="mt-6 space-y-4">
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Decision Path for SALET coloring:</h3>
          <div id="tree-path-container" class="space-y-3">
            <!-- Rendered via JS -->
          </div>
        </div>

        <!-- OCT-H Architecture Comparison Note -->
        <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-slate-800">
          <div class="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
            <div class="text-xs font-bold text-slate-400 uppercase">Input Representation</div>
            <div class="text-sm font-semibold text-white mt-1">15n Binary Features</div>
            <p class="text-xs text-slate-400 mt-1">Each guess assigns 3 bits (Green, Yellow, Gray) per position.</p>
          </div>
          <div class="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
            <div class="text-xs font-bold text-slate-400 uppercase">Tree Depth Advantage</div>
            <div class="text-sm font-semibold text-emerald-400 mt-1">Depth 8 vs Depth 12</div>
            <p class="text-xs text-slate-400 mt-1">OCT-H hyperplanes shorten decision tree by 4 layers compared to standard CART.</p>
          </div>
          <div class="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
            <div class="text-xs font-bold text-slate-400 uppercase">Interpretability</div>
            <div class="text-sm font-semibold text-indigo-400 mt-1">Human-Readable Rules</div>
            <p class="text-xs text-slate-400 mt-1">No black-box neural weights; every decision follows a sequence of simple yes/no checks.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- VIEW 3: BENCHMARK & REPORT METRICS -->
    <div id="view-metrics" class="hidden space-y-6">
      
      <!-- Top Starting Words Comparison (Paper Table 1) -->
      <div class="bg-[#141824] border border-slate-800 rounded-xl p-6 shadow-xl">
        <h2 class="text-lg font-bold text-white flex items-center gap-2 pb-4 border-b border-slate-800">
          <i class="fa-solid fa-ranking-star text-amber-400"></i> Top 5 Starting Words (Bertsimas & Paskov - Table 1)
        </h2>
        <div class="mt-4 overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="text-slate-400 uppercase border-b border-slate-800 bg-slate-900/50">
              <tr>
                <th class="py-3 px-4">Rank</th>
                <th class="py-3 px-4">Initial Guess</th>
                <th class="py-3 px-4">Expected Guesses</th>
                <th class="py-3 px-4">Max Guesses</th>
                <th class="py-3 px-4">Win Rate</th>
                <th class="py-3 px-4">Letter Composition Note</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800 mono">
              <tr class="bg-emerald-950/20 text-white font-bold">
                <td class="py-3 px-4 text-emerald-400">#1 (Optimal)</td>
                <td class="py-3 px-4 text-emerald-400 font-black tracking-wider">SALET</td>
                <td class="py-3 px-4">3.42117</td>
                <td class="py-3 px-4">&le; 5</td>
                <td class="py-3 px-4 text-emerald-400">100.0%</td>
                <td class="py-3 px-4 font-sans text-slate-300 font-normal">High-frequency A, E, T + S, L. 1.683 avg colored tiles.</td>
              </tr>
              <tr class="text-slate-300">
                <td class="py-3 px-4">#2</td>
                <td class="py-3 px-4 font-bold tracking-wider">REAST</td>
                <td class="py-3 px-4">3.42246</td>
                <td class="py-3 px-4">&le; 5</td>
                <td class="py-3 px-4">100.0%</td>
                <td class="py-3 px-4 font-sans text-slate-400">Features R, E, A, S, T</td>
              </tr>
              <tr class="text-slate-300">
                <td class="py-3 px-4">#3</td>
                <td class="py-3 px-4 font-bold tracking-wider">TRACE</td>
                <td class="py-3 px-4">3.42376</td>
                <td class="py-3 px-4">&le; 5</td>
                <td class="py-3 px-4">100.0%</td>
                <td class="py-3 px-4 font-sans text-slate-400">Features T, R, A, C, E</td>
              </tr>
              <tr class="text-slate-300">
                <td class="py-3 px-4">#4</td>
                <td class="py-3 px-4 font-bold tracking-wider">CRATE</td>
                <td class="py-3 px-4">3.42376</td>
                <td class="py-3 px-4">&le; 5</td>
                <td class="py-3 px-4">100.0%</td>
                <td class="py-3 px-4 font-sans text-slate-400">Anagram of TRACE</td>
              </tr>
              <tr class="text-slate-300">
                <td class="py-3 px-4">#5</td>
                <td class="py-3 px-4 font-bold tracking-wider">SLATE</td>
                <td class="py-3 px-4">3.42462</td>
                <td class="py-3 px-4">&le; 5</td>
                <td class="py-3 px-4">100.0%</td>
                <td class="py-3 px-4 font-sans text-slate-400">Close variant of SALET</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Comparative Baselines Table -->
      <div class="bg-[#141824] border border-slate-800 rounded-xl p-6 shadow-xl">
        <h2 class="text-lg font-bold text-white flex items-center gap-2 pb-4 border-b border-slate-800">
          <i class="fa-solid fa-code-compare text-indigo-400"></i> Comparative Benchmark Across Literature Solutions
        </h2>
        <div class="mt-4 overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="text-slate-400 uppercase border-b border-slate-800 bg-slate-900/50">
              <tr>
                <th class="py-3 px-4">Algorithm / Source</th>
                <th class="py-3 px-4">First Guess</th>
                <th class="py-3 px-4">Average Guesses</th>
                <th class="py-3 px-4">Max Guesses</th>
                <th class="py-3 px-4">Win Rate</th>
                <th class="py-3 px-4">Guaranteed Optimal?</th>
                <th class="py-3 px-4">Core Limitation</th>
              </tr>
            </thead>
            <tbody id="benchmark-tbody" class="divide-y divide-slate-800">
              <!-- Rendered via JS from benchmarks API -->
            </tbody>
          </table>
        </div>
      </div>

      <!-- Sensitivity Analysis (Paper Section 3.5 & Figure 8) -->
      <div class="bg-[#141824] border border-slate-800 rounded-xl p-6 shadow-xl">
        <div class="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <i class="fa-solid fa-chart-line text-rose-400"></i> Sensitivity Analysis: Noise Perturbation on V3*(s3)
            </h2>
            <p class="text-xs text-slate-400">Paper Section 3.5 & Figure 8 — Demonstrating why heuristic/RL approximations fail to uncover the true policy</p>
          </div>
          <span class="text-xs font-mono px-2 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">25 Simulations per Level</span>
        </div>

        <div class="mt-4 grid grid-cols-1 md:grid-cols-6 gap-3" id="sensitivity-cards">
          <!-- Rendered via JS -->
        </div>

        <div class="mt-6 p-4 bg-slate-900/60 rounded-lg border border-slate-800 text-xs text-slate-300 leading-relaxed">
          <span class="font-bold text-white">Paper Insight:</span> Even a minute <span class="text-amber-400 font-mono">0.1%</span> noise perturbation in value estimates causes error propagation that prevents recovery of the true optimal policy. At <span class="text-rose-400 font-mono">10%</span> perturbation, certainty is lost entirely and games exceed 6 guesses. This proves why 2-step greedy and approximate RL methods cannot achieve global optimality.
        </div>
      </div>

    </div>

  </main>

  <!-- Footer -->
  <footer class="border-t border-slate-800 bg-[#141824] px-6 py-4 text-center text-xs text-slate-500">
    Implementation of <span class="text-slate-400 font-medium">"An Exact and Interpretable Solution to Wordle"</span> (Dimitris Bertsimas & Alex Paskov, MIT).
  </footer>

  <script>
    // State management
    let currentSecret = 'VIXEN';
    let currentSteps = [];
    let currentStepIndex = 0;
    let isPlaying = false;
    let playTimer = null;
    let animSpeed = 900;
    let benchmarkData = null;

    // Board layout: 6 rows x 5 tiles
    function initBoard() {
      const boardEl = document.getElementById('board');
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

    // Tab switching
    function switchTab(tab) {
      ['play', 'tree', 'metrics'].forEach(t => {
        document.getElementById(`view-${t}`).classList.add('hidden');
        const btn = document.getElementById(`tab-${t}-btn`);
        btn.classList.remove('bg-emerald-600', 'text-white');
        btn.classList.add('text-slate-400');
      });
      document.getElementById(`view-${tab}`).classList.remove('hidden');
      const activeBtn = document.getElementById(`tab-${tab}-btn`);
      activeBtn.classList.remove('text-slate-400');
      activeBtn.classList.add('bg-emerald-600', 'text-white');

      if (tab === 'tree') traceTreePath();
      if (tab === 'metrics' && !benchmarkData) loadBenchmarks();
    }

    // Set word helper
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

    // Fetch simulation from backend
    async function fetchSimulation() {
      pausePlay();
      const solver = document.getElementById('solver-select').value;
      try {
        const res = await fetch(`/api/simulate?secret=${currentSecret}&solver=${solver}`);
        const data = await res.json();
        currentSteps = data.steps;
        resetPlayback();
      } catch (e) {
        console.error(e);
      }
    }

    function resetPlayback() {
      pausePlay();
      currentStepIndex = 0;
      initBoard();
      updateDiagnostics();
      document.getElementById('win-badge').classList.add('hidden');
    }

    function updateDiagnostics() {
      document.getElementById('step-indicator').innerText = `Step ${currentStepIndex} / ${currentSteps.length}`;

      if (currentStepIndex === 0) {
        document.getElementById('current-guess-pill').innerText = 'Ready to solve';
        document.getElementById('stat-candidates').innerText = '2,315';
        document.getElementById('stat-eliminated').innerText = '0 eliminated';
        document.getElementById('stat-reduction').innerText = '0%';
        document.getElementById('stat-entropy').innerText = '0.00';
        document.getElementById('stat-value').innerText = '3.42';
        document.getElementById('candidate-count-badge').innerText = '2,315 words';
        document.getElementById('partitions-container').innerHTML = '<div class="text-xs text-slate-500 text-center py-4">Press Play or Step Forward to start.</div>';
        renderCandidateCloud([]);
        return;
      }

      const step = currentSteps[currentStepIndex - 1];
      document.getElementById('current-guess-pill').innerText = `Guess: ${step.guess}`;
      document.getElementById('stat-candidates').innerText = step.candidates_after_count.toLocaleString();
      document.getElementById('stat-eliminated').innerText = `${step.eliminated_count} eliminated`;
      
      const reduction = Math.round((step.eliminated_count / step.candidates_before_count) * 100);
      document.getElementById('stat-reduction').innerText = `${reduction}%`;
      document.getElementById('stat-entropy').innerText = step.entropy_bits.toFixed(2);
      document.getElementById('stat-value').innerText = step.expected_cost.toFixed(2);
      document.getElementById('candidate-count-badge').innerText = `${step.candidates_after_count} words remaining`;

      // Render partitions breakdown
      renderPartitions(step.top_partitions, step.coloring);

      // Render candidates
      renderCandidateCloud(step.candidates_sample);

      if (step.is_won) {
        document.getElementById('win-badge').classList.remove('hidden');
        document.getElementById('win-turn').innerText = currentStepIndex;
        document.getElementById(`row-${currentStepIndex - 1}`).classList.add('win-row');
      }
    }

    function renderPartitions(parts, activeColoring) {
      const container = document.getElementById('partitions-container');
      if (!parts || parts.length === 0) {
        container.innerHTML = '<div class="text-xs text-slate-500 text-center py-2">Unique leaf state reached.</div>';
        return;
      }

      const maxCount = Math.max(...parts.map(p => p.count));
      let html = '';
      parts.forEach(p => {
        const isMatch = p.coloring === activeColoring;
        const widthPct = Math.max(8, Math.round((p.count / maxCount) * 100));
        const colorTiles = p.coloring.split('').map(c => {
          const bg = c === 'G' ? 'bg-wordle-green' : (c === 'Y' ? 'bg-wordle-yellow' : 'bg-wordle-gray');
          return `<span class="w-3 h-3 rounded-xs ${bg} inline-block"></span>`;
        }).join('');

        html += `
          <div class="flex items-center space-x-2 text-xs">
            <div class="flex items-center space-x-0.5 w-20">${colorTiles}</div>
            <div class="flex-1 bg-slate-900 rounded-full h-4 overflow-hidden p-0.5 border border-slate-800">
              <div class="h-full rounded-full transition-all duration-500 ${isMatch ? 'bg-emerald-500' : 'bg-indigo-600/70'}" style="width: ${widthPct}%"></div>
            </div>
            <span class="mono text-xs w-16 text-right ${isMatch ? 'text-emerald-400 font-bold' : 'text-slate-400'}">${p.count} words</span>
          </div>
        `;
      });
      container.innerHTML = html;
    }

    function renderCandidateCloud(words) {
      const cloud = document.getElementById('candidate-cloud');
      if (!words || words.length === 0) {
        cloud.innerHTML = '<span class="text-xs text-slate-500 italic p-2">Full word list active (2,315 candidates)</span>';
        return;
      }
      cloud.innerHTML = words.map(w => `
        <span class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono border border-slate-700 transition">
          ${w.toUpperCase()}
        </span>
      `).join('');
    }

    // Step animation logic
    function animateRow(stepIdx) {
      const step = currentSteps[stepIdx];
      const rowIdx = stepIdx;
      
      step.tile_states.forEach((tileData, colIdx) => {
        const tileEl = document.getElementById(`tile-${rowIdx}-${colIdx}`);
        const front = tileEl.querySelector('.tile-front');
        const back = tileEl.querySelector('.tile-back');

        front.innerText = tileData.letter;
        back.innerText = tileData.letter;

        // Apply color to back face
        back.classList.remove('bg-wordle-green', 'bg-wordle-yellow', 'bg-wordle-gray');
        if (tileData.state === 'green') back.classList.add('bg-wordle-green');
        else if (tileData.state === 'yellow') back.classList.add('bg-wordle-yellow');
        else back.classList.add('bg-wordle-gray');

        // Staggered flip animation
        setTimeout(() => {
          tileEl.classList.add('tile-flipped');
        }, colIdx * 100);
      });
    }

    function nextStep() {
      if (currentStepIndex < currentSteps.length) {
        animateRow(currentStepIndex);
        currentStepIndex++;
        updateDiagnostics();
        if (currentStepIndex === currentSteps.length) {
          pausePlay();
        }
      }
    }

    function prevStep() {
      if (currentStepIndex > 0) {
        currentStepIndex--;
        // Unflip row
        const rowIdx = currentStepIndex;
        for (let c = 0; c < 5; c++) {
          const tileEl = document.getElementById(`tile-${rowIdx}-${c}`);
          tileEl.classList.remove('tile-flipped');
          tileEl.querySelector('.tile-front').innerText = '';
          tileEl.querySelector('.tile-back').innerText = '';
        }
        document.getElementById(`row-${rowIdx}`).classList.remove('win-row');
        document.getElementById('win-badge').classList.add('hidden');
        updateDiagnostics();
      }
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

    // OCT-H Decision Tree Path Tracer
    async function traceTreePath() {
      const coloring = document.getElementById('tree-coloring-input').value.trim().toUpperCase();
      const container = document.getElementById('tree-path-container');
      container.innerHTML = '<div class="text-xs text-slate-500">Evaluating tree...</div>';

      try {
        const res = await fetch(`/api/tree?coloring=${coloring}`);
        const data = await res.json();
        
        let html = '';
        data.path.forEach((node, idx) => {
          if (node.is_leaf) {
            html += `
              <div class="flex items-center space-x-3 p-3 bg-emerald-950/30 border border-emerald-500/40 rounded-lg">
                <div class="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs">
                  <i class="fa-solid fa-check"></i>
                </div>
                <div>
                  <div class="text-xs uppercase font-bold text-emerald-400">Optimal Action Recommendation (Leaf)</div>
                  <div class="text-lg font-black mono text-white tracking-widest mt-0.5">GUESS: ${node.recommended_guess}</div>
                </div>
              </div>
            `;
          } else {
            const evalBadge = node.evaluated_true ? 
              '<span class="px-2 py-0.5 text-xs rounded bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30">YES (Proceed Right)</span>' :
              '<span class="px-2 py-0.5 text-xs rounded bg-slate-800 text-slate-400 font-bold border border-slate-700">NO (Proceed Left)</span>';

            html += `
              <div class="flex items-center justify-between p-3 bg-slate-900/80 border border-slate-800 rounded-lg">
                <div class="flex items-center space-x-3">
                  <span class="text-xs font-mono font-bold text-slate-500">Node #${node.node_id}</span>
                  <div class="text-xs text-slate-200">
                    Question: <strong class="text-white">${node.question}</strong>
                  </div>
                </div>
                ${evalBadge}
              </div>
            `;
          }
        });
        container.innerHTML = html;
      } catch (e) {
        console.error(e);
      }
    }

    // Load benchmarks into Metrics tab
    async function loadBenchmarks() {
      try {
        const res = await fetch('/api/benchmarks');
        benchmarkData = await res.json();
        
        // Populate table
        const tbody = document.getElementById('benchmark-tbody');
        const solvers = [
          { key: 'exact_dp', certified: true, limit: 'None (Global Optimum via Bellman)' },
          { key: 'entropy_greedy', certified: false, limit: 'Greedy 1-step myopic; blind to deep traps' },
          { key: 'two_step_greedy', certified: false, limit: 'Truncated 2-step horizon; heuristic errors' },
          { key: 'max_partitions', certified: false, limit: 'Ignores partition balance & probability' },
          { key: 'random', certified: false, limit: 'No strategic information discovery' }
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
              <td class="py-3 px-4 mono">${item.avg_guesses.toFixed(3)}</td>
              <td class="py-3 px-4 mono">${item.max_guesses}</td>
              <td class="py-3 px-4 mono ${item.win_rate >= 100 ? 'text-emerald-400' : 'text-amber-400'}">${item.win_rate.toFixed(1)}%</td>
              <td class="py-3 px-4">
                ${s.certified ? 
                  '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">YES (Certifiably Optimal)</span>' : 
                  '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-400">NO (Heuristic)</span>'}
              </td>
              <td class="py-3 px-4 text-xs font-sans text-slate-400">${s.limit}</td>
            </tr>
          `;
        });
        tbody.innerHTML = html;

        // Populate sensitivity cards
        if (benchmarkData.sensitivity_analysis && benchmarkData.sensitivity_analysis.levels) {
          const cardsEl = document.getElementById('sensitivity-cards');
          let cardsHtml = '';
          benchmarkData.sensitivity_analysis.levels.forEach(lvl => {
            cardsHtml += `
              <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
                <div class="text-xs font-mono font-bold text-rose-400">&plusmn;${lvl.perturbation_percent}% Noise</div>
                <div class="text-lg font-bold text-white mono mt-1">${lvl.median_expected_guesses.toFixed(3)}</div>
                <div class="text-[10px] text-slate-400">avg guesses</div>
                <div class="text-[10px] text-rose-400/80 mt-1 font-semibold">${lvl.certainty_risk_pct}% risk of loss</div>
              </div>
            `;
          });
          cardsEl.innerHTML = cardsHtml;
        }

      } catch (e) {
        console.error(e);
      }
    }

    // Startup
    window.addEventListener('DOMContentLoaded', () => {
      initBoard();
      fetchSimulation();
    });
  </script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quiet down console logs
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))

        elif path == '/api/simulate':
            secret = query.get('secret', ['VIXEN'])[0].strip().lower()
            solver_type = query.get('solver', ['exact_dp'])[0].strip().lower()

            try:
                steps = solver_instance.simulate_step_by_step(secret, solver_type)
                res = {'status': 'ok', 'secret': secret, 'steps': steps}
            except Exception as e:
                res = {'status': 'error', 'message': str(e)}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif path == '/api/tree':
            coloring = query.get('coloring', ['XXXXX'])[0].strip().upper()
            try:
                path_data = tree_policy.trace_path(coloring)
                res = {'status': 'ok', 'coloring': coloring, 'path': path_data}
            except Exception as e:
                res = {'status': 'error', 'message': str(e)}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif path == '/api/random':
            import random
            word = random.choice(solver_instance.solutions)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'word': word}).encode('utf-8'))

        elif path == '/api/benchmarks':
            global benchmark_cache
            if not benchmark_cache and os.path.exists(BENCHMARK_PATH):
                with open(BENCHMARK_PATH, 'r', encoding='utf-8') as f:
                    benchmark_cache = json.load(f)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(benchmark_cache or {}).encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()


def start_server():
    server = HTTPServer(('127.0.0.1', PORT), RequestHandler)
    print(f'Wordle Solver Animated UI running at http://localhost:{PORT}')
    print('Press Ctrl+C to stop.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')


if __name__ == '__main__':
    start_server()

