/**
 * Rotor Window Component (4 Drums)
 * 140ms mechanical roll animation on stepped drums.
 */

import { idx_to_char } from './types';

export class RotorDisplay {
  private container: HTMLElement;
  private drumElements: HTMLElement[] = [];
  private currentPositions: number[] = [0, 0, 0, 0];

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
  }

  private render() {
    this.container.innerHTML = `
      <div class="rotor-assembly">
        <div class="rotor-labels">
          <span>CHAKRA I (STATIC)</span>
          <span>CHAKRA II</span>
          <span>CHAKRA III</span>
          <span>CHAKRA IV (FAST)</span>
        </div>
        <div class="rotor-drums-row">
          ${[0, 1, 2, 3].map(i => `
            <div class="rotor-drum-casing">
              <div class="rotor-drum-glass">
                <div class="rotor-drum" id="drum-${i}">
                  <span class="drum-symbol">A</span>
                </div>
              </div>
              <div class="drum-bezel"></div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    this.drumElements = [0, 1, 2, 3].map(i => document.getElementById(`drum-${i}`) as HTMLElement);
  }

  public updatePositions(positions: number[], steppedFlags: boolean[]) {
    positions.forEach((pos, idx) => {
      const drum = this.drumElements[idx];
      const char = idx_to_char(pos);

      if (steppedFlags[idx]) {
        drum.classList.remove('drum-step');
        // Force reflow
        void drum.offsetWidth;
        drum.classList.add('drum-step');
      }

      const symbolEl = drum.querySelector('.drum-symbol');
      if (symbolEl) {
        symbolEl.textContent = char;
      }
      this.currentPositions[idx] = pos;
    });
  }

  public setPositionsDirect(positions: number[]) {
    positions.forEach((pos, idx) => {
      const drum = this.drumElements[idx];
      const symbolEl = drum.querySelector('.drum-symbol');
      if (symbolEl) {
        symbolEl.textContent = idx_to_char(pos);
      }
      this.currentPositions[idx] = pos;
    });
  }
}
