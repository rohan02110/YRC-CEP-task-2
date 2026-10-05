/**
 * Public & Gated Artifacts Modal
 * Dynamically passes session_id for team-specific artifacts and enforces gate-level availability.
 */

import { api } from '../net/client';
import { GatesStatus } from '../machine/types';

export class ArtifactsModal {
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
  }

  public async render() {
    const st = api.getState();
    const sessionId = st ? st.sessionId : '';

    let unlockedGates: string[] = [];
    try {
      if (st) {
        const gatesStatus: GatesStatus = await api.getGates();
        unlockedGates = gatesStatus.gates.filter(g => g.is_unlocked).map(g => g.id);
      }
    } catch {
      // If session not ready yet
    }

    const publicFiles = [
      { name: "flavor.txt", desc: "Sacred lore and the riddle of the four fragments.", gate: null },
      { name: "replica_config.json", desc: "Complete specifications and wirings for the Training Replica.", gate: null },
      { name: "ciphertext.txt", desc: "Your army's intercepted ciphertext scroll.", gate: null }
    ];

    const gate1Files = [
      { name: "enigma_spec.txt", desc: "Mathematical specification of the 30-symbol 4-of-8 machine.", gate: "I" },
      { name: "rotor_wirings.json", desc: "Sacred permutations of all 8 wheels in the pool.", gate: "I" },
      { name: "rotor_notches.json", desc: "Turnover notch positions for all 8 wheels.", gate: "I" }
    ];

    const gate2Files = [
      { name: "reflector.json", desc: "The true involutory reflector permutation of your formation.", gate: "II" },
      { name: "ring_settings.json", desc: "Ring settings (Ringstellung) for the seated wheels.", gate: "II" }
    ];

    const allFiles = [...publicFiles, ...gate1Files, ...gate2Files];

    this.container.innerHTML = `
      <div class="artifacts-panel-card">
        <div class="artifacts-header">
          <span class="artifacts-title">SANCTIONED INTELLIGENCE & SCROLLS</span>
          <span class="artifacts-subtitle">Download available reconnaissance artifacts</span>
        </div>

        <div class="artifacts-grid">
          ${allFiles.map(f => {
            const isAccessible = !f.gate || unlockedGates.includes(f.gate);
            const downloadUrl = sessionId ? `/api/v1/artifacts/${f.name}?session_id=${encodeURIComponent(sessionId)}` : `/api/v1/artifacts/${f.name}`;

            return `
              <div class="artifact-item ${isAccessible ? 'accessible' : 'gated-locked'}">
                <div class="artifact-meta">
                  <div class="artifact-title-row">
                    <span class="artifact-filename">${f.name}</span>
                    ${f.gate ? `<span class="gate-tag ${isAccessible ? 'unlocked' : 'locked'}">GATE ${f.gate} ${isAccessible ? '✓' : '🔒'}</span>` : '<span class="gate-tag public">PUBLIC</span>'}
                  </div>
                  <span class="artifact-desc">${f.desc}</span>
                </div>
                ${isAccessible ? `
                  <a href="${downloadUrl}" download="${f.name}" class="artifact-download-btn">
                    DOWNLOAD
                  </a>
                ` : `
                  <button class="artifact-download-btn disabled" disabled title="Unlock Gate ${f.gate} to access">
                    LOCKED
                  </button>
                `}
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }
}
