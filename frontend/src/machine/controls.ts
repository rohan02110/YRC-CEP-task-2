/**
 * Machine Control Strip & Interactive SVG Steckerbrett (Plugboard)
 * Handles Walzenlage, Ringstellung, Grundstellung, and cable routing up to 13 pairs.
 */

import { idx_to_char } from './types';
import { KEYBOARD_LAYOUT } from './lampboard';

export class MachineControls {
  private container: HTMLElement;
  private onConfigureCallback: (walzenlage: string[], rings: number[], grund: number[], plugboard: [string, string][]) => Promise<void>;
  private onResetCallback: () => Promise<void>;

  private walzenlage: string[] = ["I", "II", "III", "IV"];
  private ringstellung: number[] = [0, 0, 0, 0];
  private grundstellung: number[] = [0, 0, 0, 0];
  private plugboardPairs: [string, string][] = [];

  private selectedSocket: string | null = null;
  private isSealed: boolean = false;
  private resizeObserver: ResizeObserver | null = null;

  constructor(
    container: HTMLElement,
    onConfigure: (walzenlage: string[], rings: number[], grund: number[], plugboard: [string, string][]) => Promise<void>,
    onReset: () => Promise<void>
  ) {
    this.container = container;
    this.onConfigureCallback = onConfigure;
    this.onResetCallback = onReset;
    this.render();
  }

  public setSealed(sealed: boolean) {
    this.isSealed = sealed;
    const sealBadge = document.getElementById('seal-status-badge');
    if (sealBadge) {
      sealBadge.textContent = sealed ? 'FORMATION SEALED' : 'UNSEALED (CONFIGURABLE)';
      sealBadge.className = `seal-badge ${sealed ? 'sealed' : 'unsealed'}`;
    }

    const inputs = this.container.querySelectorAll<HTMLSelectElement | HTMLInputElement | HTMLButtonElement>('.control-input');
    inputs.forEach(el => {
      if (el.id !== 'reset-chakra-btn') {
        el.disabled = sealed;
      }
    });

    const sockets = this.container.querySelectorAll<HTMLElement>('.plug-socket');
    sockets.forEach(s => {
      if (sealed) {
        s.classList.add('socket-disabled');
      } else {
        s.classList.remove('socket-disabled');
      }
    });
  }

  public updateState(walzenlage: string[], rings: number[], grund: number[], pb: [string, string][], sealed: boolean) {
    this.walzenlage = [...walzenlage];
    this.ringstellung = [...rings];
    this.grundstellung = [...grund];
    this.plugboardPairs = [...pb];
    this.setSealed(sealed);
    this.syncFormValues();
    this.renderCables();
  }

  private render() {
    this.container.innerHTML = `
      <div class="controls-panel">
        <div class="controls-header">
          <div class="controls-title">CHAKRAVOORVA: ALIGNMENT & PLUGBOARD</div>
          <div id="seal-status-badge" class="seal-badge unsealed">UNSEALED (CONFIGURABLE)</div>
        </div>

        <div class="control-sections-grid">
          <!-- 1. Walzenlage -->
          <div class="control-card">
            <div class="card-label">WALZENLAGE (WHEEL ORDER)</div>
            <div class="rotor-select-row">
              ${[0, 1, 2, 3].map(i => `
                <div class="select-group">
                  <span class="slot-tag">SLOT ${i + 1}</span>
                  <select id="rotor-select-${i}" class="control-input rotor-select">
                    ${["I", "II", "III", "IV", "V", "VI", "VII", "VIII"].map(r => `
                      <option value="${r}" ${this.walzenlage[i] === r ? 'selected' : ''}>${r}</option>
                    `).join('')}
                  </select>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- 2. Ringstellung -->
          <div class="control-card">
            <div class="card-label">RINGSTELLUNG (0 - 29)</div>
            <div class="dial-inputs-row">
              ${[0, 1, 2, 3].map(i => `
                <div class="dial-group">
                  <span class="slot-tag">SLOT ${i + 1}</span>
                  <input type="number" id="ring-input-${i}" class="control-input dial-input" min="0" max="29" value="${this.ringstellung[i]}">
                </div>
              `).join('')}
            </div>
          </div>

          <!-- 3. Grundstellung -->
          <div class="control-card">
            <div class="card-label">GRUNDSTELLUNG (START POS)</div>
            <div class="dial-inputs-row">
              ${[0, 1, 2, 3].map(i => `
                <div class="dial-group">
                  <span class="slot-tag">SLOT ${i + 1}</span>
                  <select id="grund-select-${i}" class="control-input dial-select">
                    ${Array.from({ length: 30 }, (_, idx) => `
                      <option value="${idx}" ${this.grundstellung[i] === idx ? 'selected' : ''}>${idx_to_char(idx)} (${idx})</option>
                    `).join('')}
                  </select>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- 4. Interactive Steckerbrett (Plugboard) -->
        <div class="steckerbrett-panel">
          <div class="steckerbrett-header">
            <div class="card-label">STECKERBRETT (PLUGBOARD: CLICK TWO SYMBOLS TO CABLE, MAX 13 PAIRS)</div>
            <div class="steckerbrett-actions">
              <span id="plug-pairs-count" class="pair-counter">PAIRS: 0 / 13</span>
              <button id="clear-plugs-btn" class="control-input action-btn secondary-btn" type="button">CLEAR CABLES</button>
            </div>
          </div>

          <div class="steckerbrett-board-wrapper">
            <div class="steckerbrett-sockets">
              <svg id="cables-svg" class="cables-svg-overlay"></svg>
              ${KEYBOARD_LAYOUT.map(row => `
                <div class="sockets-row">
                  ${row.map(char => `
                    <div class="plug-socket" id="socket-${char}" data-char="${char}">
                      <div class="socket-hole"></div>
                      <span class="socket-letter">${char}</span>
                    </div>
                  `).join('')}
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="controls-footer-actions">
          <button id="apply-config-btn" class="control-input action-btn primary-btn" type="button">
            APPLY ALIGNMENT
          </button>
          <button id="reset-chakra-btn" class="action-btn danger-btn" type="button">
            RESET THE CHAKRA (-30 BAAN)
          </button>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  private attachEventListeners() {
    // Sockets clicking
    const sockets = this.container.querySelectorAll<HTMLElement>('.plug-socket');
    sockets.forEach(s => {
      s.addEventListener('click', () => {
        if (this.isSealed) return;
        const char = s.getAttribute('data-char');
        if (!char) return;
        this.handleSocketClick(char);
      });
    });

    // Clear cables
    const clearBtn = document.getElementById('clear-plugs-btn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (this.isSealed) return;
        this.plugboardPairs = [];
        this.selectedSocket = null;
        this.renderCables();
      });
    }

    // Apply config
    const applyBtn = document.getElementById('apply-config-btn');
    if (applyBtn) {
      applyBtn.addEventListener('click', () => {
        if (this.isSealed) return;
        this.collectAndApply();
      });
    }

    // Reset Chakra
    const resetBtn = document.getElementById('reset-chakra-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.onResetCallback();
      });
    }

    // Auto re-render cables on layout, container size, and fullscreen changes
    const socketsContainer = this.container.querySelector('.steckerbrett-sockets');
    if (socketsContainer && typeof ResizeObserver !== 'undefined') {
      this.resizeObserver = new ResizeObserver(() => {
        window.requestAnimationFrame(() => this.renderCables());
      });
      this.resizeObserver.observe(socketsContainer);
    }

    window.addEventListener('resize', () => {
      window.requestAnimationFrame(() => this.renderCables());
    });

    document.addEventListener('fullscreenchange', () => {
      window.requestAnimationFrame(() => this.renderCables());
    });
  }

  private handleSocketClick(char: string) {
    // Check if socket already plugged -> remove existing pair
    const existingIdx = this.plugboardPairs.findIndex(([a, b]) => a === char || b === char);
    if (existingIdx !== -1) {
      this.plugboardPairs.splice(existingIdx, 1);
      this.selectedSocket = null;
      this.renderCables();
      return;
    }

    if (!this.selectedSocket) {
      // First socket selected
      this.selectedSocket = char;
      const sockEl = document.getElementById(`socket-${char}`);
      if (sockEl) sockEl.classList.add('socket-selected');
    } else {
      // Second socket selected
      const first = this.selectedSocket;
      this.selectedSocket = null;
      const sock1 = document.getElementById(`socket-${first}`);
      if (sock1) sock1.classList.remove('socket-selected');

      if (first !== char) {
        if (this.plugboardPairs.length < 13) {
          const pair: [string, string] = [first < char ? first : char, first < char ? char : first];
          this.plugboardPairs.push(pair);
          this.renderCables();
        }
      }
    }
  }

  private renderCables() {
    const svg = document.getElementById('cables-svg') as unknown as SVGSVGElement;
    if (!svg) return;

    svg.innerHTML = '';
    const counter = document.getElementById('plug-pairs-count');
    if (counter) {
      counter.textContent = `PAIRS: ${this.plugboardPairs.length} / 13`;
    }

    // Clear socket highlight classes
    document.querySelectorAll('.plug-socket').forEach(s => {
      s.classList.remove('socket-plugged', 'socket-selected');
    });

    if (this.selectedSocket) {
      const sel = document.getElementById(`socket-${this.selectedSocket}`);
      if (sel) sel.classList.add('socket-selected');
    }

    if (this.plugboardPairs.length === 0) return;

    const boardRect = svg.getBoundingClientRect();
    if (boardRect.width === 0 || boardRect.height === 0) return;

    const CABLE_COLORS = [
      '#C8892B', '#E5A63F', '#D15822', '#A33322',
      '#6E8C4E', '#4B7B9E', '#8C5B9E', '#9E8C4E',
      '#C85B5B', '#4E9E8C', '#8C9E4E', '#B87B4E', '#8C7B6E'
    ];

    this.plugboardPairs.forEach(([a, b], idx) => {
      const elA = document.getElementById(`socket-${a}`);
      const elB = document.getElementById(`socket-${b}`);
      if (!elA || !elB) return;

      elA.classList.add('socket-plugged');
      elB.classList.add('socket-plugged');

      const holeA = elA.querySelector('.socket-hole') || elA;
      const holeB = elB.querySelector('.socket-hole') || elB;

      const rectA = holeA.getBoundingClientRect();
      const rectB = holeB.getBoundingClientRect();

      const x1 = rectA.left + rectA.width / 2 - boardRect.left;
      const y1 = rectA.top + rectA.height / 2 - boardRect.top;
      const x2 = rectB.left + rectB.width / 2 - boardRect.left;
      const y2 = rectB.top + rectB.height / 2 - boardRect.top;

      const color = CABLE_COLORS[idx % CABLE_COLORS.length];
      const dx = Math.abs(x2 - x1);
      const dy = Math.abs(y2 - y1);
      const midY = (y1 + y2) / 2 + Math.max(20, dx * 0.2 + dy * 0.1);

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', `M ${x1.toFixed(1)} ${y1.toFixed(1)} Q ${((x1 + x2) / 2).toFixed(1)} ${midY.toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)}`);
      path.setAttribute('stroke', color);
      path.setAttribute('stroke-width', '4');
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke-linecap', 'round');
      path.setAttribute('class', 'plug-cable-path');

      svg.appendChild(path);
    });
  }

  private syncFormValues() {
    [0, 1, 2, 3].forEach(i => {
      const rotSel = document.getElementById(`rotor-select-${i}`) as HTMLSelectElement;
      if (rotSel) rotSel.value = this.walzenlage[i];

      const ringIn = document.getElementById(`ring-input-${i}`) as HTMLInputElement;
      if (ringIn) ringIn.value = this.ringstellung[i].toString();

      const grundSel = document.getElementById(`grund-select-${i}`) as HTMLSelectElement;
      if (grundSel) grundSel.value = this.grundstellung[i].toString();
    });
  }

  private collectAndApply() {
    const newWalzenlage: string[] = [];
    const newRings: number[] = [];
    const newGrund: number[] = [];

    for (let i = 0; i < 4; i++) {
      const rotSel = document.getElementById(`rotor-select-${i}`) as HTMLSelectElement;
      newWalzenlage.push(rotSel ? rotSel.value : 'I');

      const ringIn = document.getElementById(`ring-input-${i}`) as HTMLInputElement;
      newRings.push(ringIn ? parseInt(ringIn.value, 10) % 30 : 0);

      const grundSel = document.getElementById(`grund-select-${i}`) as HTMLSelectElement;
      newGrund.push(grundSel ? parseInt(grundSel.value, 10) % 30 : 0);
    }

    this.onConfigureCallback(newWalzenlage, newRings, newGrund, this.plugboardPairs);
  }
}
