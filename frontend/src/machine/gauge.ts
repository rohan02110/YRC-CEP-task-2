/**
 * Baan (Arrow) Gauge & Lockout Notification Banner
 */

export class GaugeDisplay {
  private container: HTMLElement;
  private baanCountEl: HTMLElement | null = null;
  private capCountEl: HTMLElement | null = null;
  private lockBannerEl: HTMLElement | null = null;
  private lockCountdownEl: HTMLElement | null = null;
  private lockReasonEl: HTMLElement | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
  }

  private render() {
    this.container.innerHTML = `
      <div class="gauge-container">
        <div class="gauge-card baan-card">
          <div class="gauge-icon">🏹</div>
          <div class="gauge-info">
            <span class="gauge-label">BAAN (ARROWS) REMAINING</span>
            <div class="gauge-value-row">
              <span id="baan-count" class="gauge-number">400</span>
              <span class="gauge-max">/ 400</span>
            </div>
          </div>
        </div>

        <div class="gauge-card lifetime-card">
          <div class="gauge-icon">⚡</div>
          <div class="gauge-info">
            <span class="gauge-label">LIFETIME FORMATION CAP</span>
            <div class="gauge-value-row">
              <span id="cap-count" class="gauge-number">2000</span>
              <span class="gauge-max">/ 2000</span>
            </div>
          </div>
        </div>

        <div id="lockout-banner" class="lockout-banner hidden">
          <div class="lockout-header">
            <span class="lockout-icon">🔒</span>
            <span class="lockout-title">FORMATION LOCKED BY DHARMA</span>
          </div>
          <div id="lockout-reason" class="lockout-reason"></div>
          <div class="lockout-timer-row">
            <span>RESUMES IN: </span>
            <span id="lockout-countdown" class="lockout-countdown">0s</span>
          </div>
        </div>
      </div>
    `;

    this.baanCountEl = document.getElementById('baan-count');
    this.capCountEl = document.getElementById('cap-count');
    this.lockBannerEl = document.getElementById('lockout-banner');
    this.lockCountdownEl = document.getElementById('lockout-countdown');
    this.lockReasonEl = document.getElementById('lockout-reason');
  }

  public updateStatus(baan: number, lifetimeCap: number, isLocked: boolean, lockSeconds: number, lockReason: string | null) {
    if (this.baanCountEl) this.baanCountEl.textContent = baan.toString();
    if (this.capCountEl) this.capCountEl.textContent = lifetimeCap.toString();

    if (this.lockBannerEl) {
      if (isLocked) {
        this.lockBannerEl.classList.remove('hidden');
        if (this.lockCountdownEl) this.lockCountdownEl.textContent = `${lockSeconds}s`;
        if (this.lockReasonEl) this.lockReasonEl.textContent = lockReason || 'Violation detected';
      } else {
        this.lockBannerEl.classList.add('hidden');
      }
    }
  }
}
