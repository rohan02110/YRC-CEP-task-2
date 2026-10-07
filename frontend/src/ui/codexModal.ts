/**
 * Battlefield Codex Modal & Storyline Workflow Guide (v2 Hardened)
 * Immersive Mahabharata Lore, Seven Celestial Gates, Dual Machine Modes, and Laws of Dharma.
 * Zero leaks of internal cribs, wirings, or plaintext conventions.
 */

import { sound } from '../audio/synth';

export class CodexModal {
  private overlay: HTMLElement;

  constructor() {
    this.overlay = document.createElement('div');
    this.overlay.id = 'codex-modal-overlay';
    this.overlay.className = 'codex-modal-overlay hidden';
    document.body.appendChild(this.overlay);

    this.render();
    this.attachEvents();
  }

  private render() {
    this.overlay.innerHTML = `
      <div class="codex-modal-container">
        <!-- Header -->
        <div class="codex-header">
          <div class="codex-title-group">
            <span class="codex-icon">☸️</span>
            <div>
              <h2 class="codex-title">THE BATTLEFIELD CODEX</h2>
              <span class="codex-subtitle">WAR OF KURUKSHETRA &bull; DAY 13 &bull; TACTICAL BRIEFING & GATES OF DHARMA</span>
            </div>
          </div>
          <button id="codex-close-btn" class="codex-close-btn" type="button" title="Close Codex (Esc)">&times;</button>
        </div>

        <!-- Navigation Tabs -->
        <div class="codex-nav-tabs">
          <button class="codex-tab-btn active" data-tab="story">📜 The Legend of Day 13</button>
          <button class="codex-tab-btn" data-tab="workflow">⚔️ Tactical Workflow (Gates & Strategy)</button>
          <button class="codex-tab-btn" data-tab="machine">☸️ Training Replica & Modes</button>
          <button class="codex-tab-btn" data-tab="dharma">🛡️ Laws of Dharma & Rules</button>
        </div>

        <!-- Modal Body / Tab Content -->
        <div class="codex-content-body">
          
          <!-- TAB 1: STORYLINE -->
          <div id="tab-story" class="codex-tab-pane active">
            <div class="story-chapter">
              <div class="chapter-badge">ACT I: THE SEVENTH TIER</div>
              <h3 class="chapter-title">The Fall of Dawn on the Thirteenth Day</h3>
              <p>
                The sun rose crimson over the plains of <strong>Kurukshetra</strong>. With Arjuna lured far to the south by the suicidal charge of the Samsaptaka warriors, Acharya Drona—supreme commander of the Kaurava hosts—unfurled his masterpiece: the <strong>Chakravyuha</strong> (चक्रव्यूह).
              </p>
              <p>
                A vast, rotating labyrinth of concentric warrior rings, the Chakravyuha spun with the precision of celestial wheels. Millions of infantry, armored elephants, and Maharathis marched in continuous orbits. Any warrior who entered without knowing its sacred mathematical cycle would be disoriented, surrounded, and crushed.
              </p>
            </div>

            <div class="story-chapter">
              <div class="chapter-badge">ACT II: THE WARRIOR'S INHERITANCE</div>
              <h3 class="chapter-title">Abhimanyu's Sacred Duty</h3>
              <p>
                Among all the remaining Pandava generals, only sixteen-year-old <strong>Abhimanyu</strong>—son of Arjuna and Subhadra—knew the secret to pierce the outer perimeter. While yet in his mother's womb, he had listened as Arjuna explained the intricate maneuvers required to enter the spiral.
              </p>
              <p>
                Yet, before Arjuna could reveal how to break through the innermost sanctum, Subhadra had fallen asleep. Abhimanyu entered fearlessly, shattering tier after tier with celestial arrows, but found himself face-to-face with Drona's command redoubt.
              </p>
            </div>

            <div class="story-chapter">
              <div class="chapter-badge">ACT III: THE CIPHER & THE GATES</div>
              <h3 class="chapter-title">The Gated Chakravyuha Formation</h3>
              <p>
                Pandava scouts have intercepted your army's encrypted battle scroll: <code>ciphertext.txt</code>. Transmitted through the Kaurava lines, it carries the celestial battle orders and the coordinates of the <strong>Sacred Flag</strong>.
              </p>
              <p>
                Drona has locked the inner mechanics behind progressive celestial seals. To triumph, your army must earn the sacred seals of the earlier trials, unlock the Gates of Dharma, test hypotheses against the Training Replica, and command the Original machine to reveal the truth!
              </p>
            </div>
          </div>

          <!-- TAB 2: WORKFLOW -->
          <div id="tab-workflow" class="codex-tab-pane">
            <div class="workflow-intro">
              <h3>THE 5-PHASE CAMPAIGN PROTOCOL</h3>
              <p>Follow these military steps to break Drona's cipher and claim the sacred Flag:</p>
            </div>

            <div class="workflow-timeline">
              
              <!-- Step 1 -->
              <div class="workflow-step-card">
                <div class="step-number">01</div>
                <div class="step-content">
                  <div class="step-header">
                    <h4>Analyze Public Intelligence & Riddle</h4>
                    <span class="step-tag">PUBLIC SCROLLS</span>
                  </div>
                  <p>
                    Download <code>flavor.txt</code> and <code>ciphertext.txt</code>. Read the four ancient riddle fragments in <code>flavor.txt</code> to deduce the structure of the message, the identity of the opener, the idle scribe strokes, and the rearranging of the tongue.
                  </p>
                </div>
              </div>

              <!-- Step 2 -->
              <div class="workflow-step-card">
                <div class="step-number">02</div>
                <div class="step-content">
                  <div class="step-header">
                    <h4>Unit Test with the Training Replica</h4>
                    <span class="step-tag">REPLICA WORKSHOP</span>
                  </div>
                  <p>
                    Use <code>replica_config.json</code> to build and calibrate your offline simulator. Verify that your stepping mechanics, reciprocal reflector, and plugboard logic match the server-side machine exactly.
                  </p>
                </div>
              </div>

              <!-- Step 3 -->
              <div class="workflow-step-card">
                <div class="step-number">03</div>
                <div class="step-content">
                  <div class="step-header">
                    <h4>Offer Seals to Unlock Celestial Gates</h4>
                    <span class="step-tag">GATE UNLOCKS</span>
                  </div>
                  <p>
                    Offer the Seal of Gandiva (Challenge 1 flag) to Gate I to reveal wheel wirings and specifications. Offer the Seal of Sanjaya (Challenge 2 flag) to Gate II to reveal the true reflector, ring settings, and engage the Original Machine.
                  </p>
                </div>
              </div>

              <!-- Step 4 -->
              <div class="workflow-step-card">
                <div class="step-number">04</div>
                <div class="step-content">
                  <div class="step-header">
                    <h4>Deduce Wheel Order & Plugboard Alignment</h4>
                    <span class="step-tag">OFFLINE SEARCH</span>
                  </div>
                  <p>
                    With the revealed pool of 8 wheels, reflector, and rings, run your offline cryptanalysis against the deduced opener and substitution layer to isolate the seated wheels, start positions, and plugboard pairs.
                  </p>
                </div>
              </div>

              <!-- Step 5 -->
              <div class="workflow-step-card">
                <div class="step-number">05</div>
                <div class="step-content">
                  <div class="step-header">
                    <h4>Undo the Rearranged Tongue & Claim Flag</h4>
                    <span class="step-tag">FLAG SUBMISSION</span>
                  </div>
                  <p>
                    Reversing the machine gives the intermediate layer. Invert the keyword substitution to recover the full bilingual narrative ending in your team's flag format <code>KCTF{...}</code>. Submit the recovered flag to the CTF platform to claim victory!
                  </p>
                </div>
              </div>

            </div>
          </div>

          <!-- TAB 3: MACHINE MECHANICS -->
          <div id="tab-machine" class="codex-tab-pane">
            <div class="mechanics-grid">
              
              <div class="mech-card">
                <h4>🔤 Extended 30-Symbol Alphabet ($N=30$)</h4>
                <div class="code-snippet-box">
                  <code>ABCDEFGHIJKLMNOPQRSTUVWXYZ{}#_</code>
                </div>
                <p>
                  <strong>Total Symbols:</strong> 30 celestial characters.
                </p>
                <p>
                  All machine transformations, wirings, reflectors, and plugboards operate strictly within this 30-symbol set.
                </p>
              </div>

              <div class="mech-card">
                <h4>🔄 The Stepping Mechanics</h4>
                <p>
                  The machine seats 4 wheels chosen from the available pool.
                </p>
                <p>
                  The rightmost wheel advances on every keypress. Middle wheels advance when their right neighbor is on a notch position. The leftmost wheel remains stationary during operation.
                </p>
              </div>

              <div class="mech-card">
                <h4>⚙️ Dual Machine Modes</h4>
                <p>
                  <strong>Training Replica:</strong> Uses public wirings from <code>replica_config.json</code> with its own independent arrow quota.
                </p>
                <p>
                  <strong>Original Engine:</strong> Available after Gate II, loaded with your army's true wirings and reflector.
                </p>
              </div>

              <div class="mech-card">
                <h4>🔌 The Plugboard (Steckerbrett)</h4>
                <p>
                  Allows bilateral swapping of symbol pairs before and after passing through the wheel core. Signals pass symmetrically through the board on entry and return.
                </p>
              </div>

            </div>
          </div>

          <!-- TAB 4: LAWS OF DHARMA -->
          <div id="tab-dharma" class="codex-tab-pane">
            <div class="dharma-rules-container">
              
              <div class="dharma-rule-card">
                <div class="rule-icon">🏹</div>
                <div class="rule-details">
                  <h4>Quiver Limits (Baan Management)</h4>
                  <p>
                    Each keypress consumes <strong>1 Baan</strong>. Reconfiguring or resetting the machine costs <strong>30 Baan</strong>. Baan refills at 400/hr up to capacity. Max lifetime cap is 2000 arrows.
                  </p>
                </div>
              </div>

              <div class="dharma-rule-card">
                <div class="rule-icon">⚖️</div>
                <div class="rule-details">
                  <h4>Penalty Ladders & Lockouts</h4>
                  <p>
                    Incorrect flag submissions and rejected gate seals trigger exponential lockout timers (capped at 5 minutes maximum). Fast automated scraping triggers soft violation escalations.
                  </p>
                </div>
              </div>

              <div class="dharma-rule-card">
                <div class="rule-icon">🛡️</div>
                <div class="rule-details">
                  <h4>Anti-Collusion & Integrity</h4>
                  <p>
                    Every team commands a unique deterministic instance. Submitting another army's flag or decoy banners triggers immediate hard strikes and administrative alerts.
                  </p>
                </div>
              </div>

            </div>
          </div>

        </div>
      </div>
    `;
  }

  private attachEvents() {
    const closeBtn = this.overlay.querySelector('#codex-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hide());
    }

    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        this.hide();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !this.overlay.classList.contains('hidden')) {
        this.hide();
      }
    });

    const tabBtns = this.overlay.querySelectorAll<HTMLButtonElement>('.codex-tab-btn');
    tabBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');
        if (targetTab) {
          sound.playRelayThunk();
          this.switchTab(targetTab);
        }
      });
    });
  }

  public show(tab: string = 'story') {
    sound.playChakraHum();
    this.switchTab(tab);
    this.overlay.classList.remove('hidden');
  }

  public hide() {
    this.overlay.classList.add('hidden');
  }

  private switchTab(tabId: string) {
    const tabBtns = this.overlay.querySelectorAll<HTMLButtonElement>('.codex-tab-btn');
    tabBtns.forEach((btn) => {
      if (btn.getAttribute('data-tab') === tabId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    const panes = this.overlay.querySelectorAll<HTMLElement>('.codex-tab-pane');
    panes.forEach((pane) => {
      if (pane.id === `tab-${tabId}`) {
        pane.classList.add('active');
      } else {
        pane.classList.remove('active');
      }
    });
  }
}
