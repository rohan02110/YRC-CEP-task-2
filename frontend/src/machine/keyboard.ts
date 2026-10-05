/**
 * 30-Key Interactive Mechanical Keyboard
 * Serialized request queue: drops requests if queue exceeds 4 ("keys jam").
 */

import { KEYBOARD_LAYOUT } from './lampboard';

export class Keyboard {
  private container: HTMLElement;
  private onKeyPressCallback: (char: string) => Promise<void>;
  private keyMap: Map<string, HTMLElement> = new Map();
  private queue: string[] = [];
  private isProcessing: boolean = false;
  private isEnabled: boolean = true;

  constructor(container: HTMLElement, onKeyPress: (char: string) => Promise<void>) {
    this.container = container;
    this.onKeyPressCallback = onKeyPress;
    this.render();
  }

  private render() {
    this.container.innerHTML = `
      <div class="keyboard-casing">
        ${KEYBOARD_LAYOUT.map((row, rIdx) => `
          <div class="keyboard-row row-${rIdx}">
            ${row.map(char => `
              <button class="key" id="key-${char}" data-char="${char}" type="button">
                <div class="key-cap">
                  <span class="key-letter">${char}</span>
                </div>
                <div class="key-plunger"></div>
              </button>
            `).join('')}
          </div>
        `).join('')}
      </div>
    `;

    KEYBOARD_LAYOUT.flat().forEach(char => {
      const btn = document.getElementById(`key-${char}`) as HTMLButtonElement;
      if (btn) {
        this.keyMap.set(char, btn);
        btn.addEventListener('mousedown', (e) => {
          e.preventDefault();
          this.triggerKey(char);
        });
      }
    });
  }

  public setEnabled(enabled: boolean) {
    this.isEnabled = enabled;
    this.keyMap.forEach(btn => {
      (btn as HTMLButtonElement).disabled = !enabled;
    });
  }

  public triggerKey(char: string) {
    if (!this.isEnabled) return;
    const upper = char.toUpperCase();
    const btn = this.keyMap.get(upper);

    if (btn) {
      btn.classList.add('key-pressed');
      setTimeout(() => btn.classList.remove('key-pressed'), 120);
    }

    if (this.queue.length >= 4) {
      // Key jamming: drop press
      if (btn) {
        btn.classList.add('key-jammed');
        setTimeout(() => btn.classList.remove('key-jammed'), 250);
      }
      return;
    }

    this.queue.push(upper);
    this.processQueue();
  }

  private async processQueue() {
    if (this.isProcessing || this.queue.length === 0) return;
    this.isProcessing = true;

    while (this.queue.length > 0) {
      const nextChar = this.queue.shift();
      if (nextChar) {
        try {
          await this.onKeyPressCallback(nextChar);
        } catch {
          // Drop queue on hard error
          this.queue = [];
        }
      }
    }

    this.isProcessing = false;
  }
}
