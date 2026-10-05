/**
 * Seven Gates UI Component
 * Progressive unlock panel for Gate I (Seal of Gandiva) and Gate II (Seal of Sanjaya).
 * Handles unlock submission, locked timers, radiant unlock animations, and mode switching.
 */

import { api } from '../net/client';
import { sound } from '../audio/synth';
import { GatesStatus, HintItem } from '../machine/types';

export class GatesPanel {
  private mount: HTMLElement;
  private modal: HTMLElement | null = null;
  private onModeSwitched: (() => void) | null = null;

  constructor(mount: HTMLElement, onModeSwitched?: () => void) {
    this.mount = mount;
    this.onModeSwitched = onModeSwitched || null;
    this.renderTrigger();
  }

  private renderTrigger() {
    this.mount.innerHTML = `
      <div class="gates-trigger-card">
        <div class="gates-summary-header">
          <span class="gates-sacred-icon">☸</span>
          <span class="gates-title">SEVEN CELESTIAL GATES</span>
        </div>
        <button id="open-gates-btn" class="kuru-btn primary-btn gates-open-action">ENTER GATES OF DHARMA</button>
      </div>
    `;

    const openBtn = this.mount.querySelector('#open-gates-btn');
    if (openBtn) {
      openBtn.addEventListener('click', () => this.showModal());
    }
  }

  public async showModal() {
    if (this.modal) {
      this.modal.remove();
    }

    this.modal = document.createElement('div');
    this.modal.className = 'kuru-modal-backdrop active';
    this.modal.innerHTML = `
      <div class="kuru-modal-dialog gates-dialog">
        <div class="modal-header">
          <h2><span class="gold-symbol">☸</span> THE SEVEN GATES OF CHAKRAVYUHA</h2>
          <button class="modal-close-btn" id="gates-close-btn">✕</button>
        </div>
        <div class="modal-body gates-body">
          <div class="gates-mode-banner" id="gates-mode-banner">
            <span class="mode-label">CURRENT MACHINE MODE:</span>
            <span class="mode-badge replica" id="gates-current-mode">TRAINING REPLICA</span>
          </div>

          <p class="gates-intro">
            Drona has fortified the Chakravyuha behind progressive celestial seals. 
            Offer the sacred seals acquired from previous trials to pierce through each tier.
          </p>

          <div class="gates-list-container" id="gates-list">
            <div class="loading-spinner">Consulting the stars...</div>
          </div>

          <div class="hints-section" id="hints-section">
            <h3><span class="gold-symbol">📜</span> REVEALED INSPIRATIONS (HINTS)</h3>
            <div id="hints-list" class="hints-list">
              <p class="no-hints">No divine inspirations have been revealed yet.</p>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(this.modal);

    const closeBtn = this.modal.querySelector('#gates-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hideModal());
    }

    await this.refreshGates();
    await this.refreshHints();
  }

  public hideModal() {
    if (this.modal) {
      this.modal.remove();
      this.modal = null;
    }
  }

  private async refreshGates() {
    if (!this.modal) return;
    const listEl = this.modal.querySelector('#gates-list');
    const modeBadge = this.modal.querySelector('#gates-current-mode');
    if (!listEl) return;

    try {
      const status: GatesStatus = await api.getGates();
      if (modeBadge) {
        if (status.current_mode === 'original') {
          modeBadge.textContent = 'ORIGINAL CELESTIAL ENGINE';
          modeBadge.className = 'mode-badge original';
        } else {
          modeBadge.textContent = 'TRAINING REPLICA';
          modeBadge.className = 'mode-badge replica';
        }
      }

      listEl.innerHTML = status.gates.map((g, idx) => `
        <div class="gate-card ${g.is_unlocked ? 'unlocked' : 'locked'}" id="gate-card-${g.id}">
          <div class="gate-card-header">
            <div class="gate-title-group">
              <span class="gate-numeral">GATE ${g.id}</span>
              <span class="gate-name">${g.name}</span>
            </div>
            <span class="gate-status-pill ${g.is_unlocked ? 'unlocked' : 'locked'}">
              ${g.is_unlocked ? '✓ UNLOCKED' : '🔒 SEALED'}
            </span>
          </div>

          <div class="gate-card-body">
            ${g.is_unlocked ? `
              <div class="unlocked-msg">
                <span class="gold-check">✧</span> Sacred Seal accepted. Intelligence revealed to your army.
                ${g.id === 'II' && status.current_mode !== 'original' ? `
                  <div class="engage-original-box">
                    <p>The Original Celestial Machine is now ready to be commanded.</p>
                    <button class="kuru-btn accent-btn" id="engage-original-btn">ENGAGE ORIGINAL MACHINE</button>
                  </div>
                ` : ''}
              </div>
            ` : `
              <div class="locked-form">
                <p class="gate-desc">${idx === 0 ? 'Offer the seal of the first trial (Challenge 1 flag).' : 'Offer the seal of the second trial (Challenge 2 flag).'}</p>
                <div class="gate-input-row">
                  <input type="text" class="kuru-input gate-seal-input" id="gate-seal-input-${g.id}" placeholder="Enter sacred seal..." ${g.is_locked ? 'disabled' : ''} />
                  <button class="kuru-btn primary-btn gate-unlock-btn" data-gate-id="${g.id}" ${g.is_locked ? 'disabled' : ''}>
                    OFFER SEAL
                  </button>
                </div>
                ${g.is_locked ? `<div class="gate-lockout-msg">⏱ Gate is sealed for ${g.lock_remaining_seconds}s.</div>` : ''}
                <div class="gate-feedback" id="gate-feedback-${g.id}"></div>
              </div>
            `}
          </div>
        </div>
      `).join('');

      // Attach event listeners
      status.gates.forEach((g) => {
        const btn = listEl.querySelector(`[data-gate-id="${g.id}"]`);
        if (btn) {
          btn.addEventListener('click', () => this.handleUnlock(g.id));
        }
      });

      const engageBtn = listEl.querySelector('#engage-original-btn');
      if (engageBtn) {
        engageBtn.addEventListener('click', async () => {
          sound.playChakraHum();
          try {
            await api.switchMode('original');
            if (this.onModeSwitched) this.onModeSwitched();
            await this.refreshGates();
          } catch (err: unknown) {
            alert((err as Error).message || 'Mode switch failed');
          }
        });
      }
    } catch (err: unknown) {
      listEl.innerHTML = `<div class="error-box">${(err as Error).message || 'Failed to load gates'}</div>`;
    }
  }

  private async handleUnlock(gateId: string) {
    if (!this.modal) return;
    const input = this.modal.querySelector(`#gate-seal-input-${gateId}`) as HTMLInputElement;
    const feedback = this.modal.querySelector(`#gate-feedback-${gateId}`) as HTMLElement;
    if (!input || !input.value.trim()) return;

    const seal = input.value.trim();
    sound.playRelayThunk();

    try {
      feedback.textContent = 'Offering seal to the celestial wardens...';
      feedback.className = 'gate-feedback pending';

      const res = await api.unlockGate(gateId, seal);
      if (res.success) {
        sound.playChakraHum();
        feedback.textContent = res.message;
        feedback.className = 'gate-feedback success';

        const card = this.modal.querySelector(`#gate-card-${gateId}`);
        if (card) {
          card.classList.add('radiant-burst');
        }

        setTimeout(() => this.refreshGates(), 800);
      } else {
        feedback.textContent = res.message;
        feedback.className = 'gate-feedback error';
        setTimeout(() => this.refreshGates(), 1200);
      }
    } catch (err: unknown) {
      feedback.textContent = (err as Error).message || 'Submission rejected.';
      feedback.className = 'gate-feedback error';
    }
  }

  private async refreshHints() {
    if (!this.modal) return;
    const hintsEl = this.modal.querySelector('#hints-list');
    if (!hintsEl) return;

    try {
      const hints: HintItem[] = await api.getHints();
      if (!hints || hints.length === 0) {
        hintsEl.innerHTML = `<p class="no-hints">No divine inspirations have been released yet by the organizers.</p>`;
        return;
      }

      hintsEl.innerHTML = hints.map((h) => `
        <div class="hint-card">
          <div class="hint-header">
            <span class="hint-id">INSPIRATION #${h.id}</span>
            <span class="hint-title">${h.title}</span>
          </div>
          <p class="hint-text">${h.text}</p>
        </div>
      `).join('');
    } catch {
      hintsEl.innerHTML = `<p class="no-hints">Inspirations temporarily unreachable.</p>`;
    }
  }
}
