/**
 * Flag Submission Panel
 * "Offer the answer to Dharma." Typed input only (paste blocked).
 */

import { api } from '../net/client';
import { sound } from '../audio/synth';

export class FlagSubmissionPanel {
  private container: HTMLElement;
  private inputEl: HTMLInputElement | null = null;
  private statusEl: HTMLElement | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
  }

  private render() {
    this.container.innerHTML = `
      <div class="flag-panel-card">
        <div class="flag-panel-header">
          <span class="flag-title">OFFER THE SACRED ANSWER TO DHARMA</span>
          <span class="flag-format-hint">FORMAT: KCTF{...}</span>
        </div>

        <form id="flag-form" class="flag-form-row">
          <input
            type="text"
            id="flag-input"
            class="flag-input-field"
            placeholder="Type your recovered flag here..."
            autocomplete="off"
            spellcheck="false"
            autocapitalize="off"
            autocorrect="off"
            onpaste="return false;"
            oncopy="return false;"
            oncut="return false;"
            ondrop="return false;"
          />
          <button type="submit" id="flag-submit-btn" class="flag-submit-button">
            SUBMIT TO DHARMA
          </button>
        </form>

        <div id="flag-feedback" class="flag-feedback-msg hidden"></div>
      </div>
    `;

    this.inputEl = document.getElementById('flag-input') as HTMLInputElement;
    this.statusEl = document.getElementById('flag-feedback');

    const form = document.getElementById('flag-form');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleSubmit();
      });
    }
  }

  private async handleSubmit() {
    if (!this.inputEl || !this.statusEl) return;
    const flagVal = this.inputEl.value.trim();
    if (!flagVal) return;

    sound.playRelayThunk();

    try {
      this.statusEl.className = 'flag-feedback-msg info';
      this.statusEl.textContent = 'Evaluating your offering against cosmic law...';
      this.statusEl.classList.remove('hidden');

      const res = await api.submitFlag(flagVal);

      if (res.correct) {
        this.statusEl.className = 'flag-feedback-msg victory';
        this.statusEl.textContent = `VICTORY! ${res.message}`;
      } else {
        this.statusEl.className = 'flag-feedback-msg error';
        this.statusEl.textContent = `REJECTED: ${res.message}`;
      }
    } catch (err: unknown) {
      this.statusEl.className = 'flag-feedback-msg error';
      this.statusEl.textContent = `ERROR: ${(err as Error).message}`;
    }
  }
}
