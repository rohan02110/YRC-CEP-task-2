/**
 * 30-Lamp Lampboard Component
 * 3 Rows of 10 Lamps:
 * Row 1: Q W E R T Y U I O P
 * Row 2: A S D F G H J K L {
 * Row 3: Z X C V B N M } _ #
 */

export const KEYBOARD_LAYOUT = [
  ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
  ["A", "S", "D", "F", "G", "H", "J", "K", "L", "{" ],
  ["Z", "X", "C", "V", "B", "N", "M", "}", "_", "#"]
];

export class Lampboard {
  private container: HTMLElement;
  private lampMap: Map<string, HTMLElement> = new Map();
  private activeTimeout: number | null = null;
  private currentActiveLamp: HTMLElement | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
  }

  private render() {
    this.container.innerHTML = `
      <div class="lampboard-casing">
        ${KEYBOARD_LAYOUT.map((row, rIdx) => `
          <div class="lampboard-row row-${rIdx}">
            ${row.map(char => `
              <div class="lamp" id="lamp-${char}" data-char="${char}">
                <div class="lamp-bulb">
                  <span class="lamp-letter">${char}</span>
                </div>
                <div class="lamp-socket"></div>
              </div>
            `).join('')}
          </div>
        `).join('')}
      </div>
    `;

    KEYBOARD_LAYOUT.flat().forEach(char => {
      const el = document.getElementById(`lamp-${char}`);
      if (el) this.lampMap.set(char, el);
    });
  }

  public lightLamp(char: string) {
    this.clearLamp();

    const lamp = this.lampMap.get(char.toUpperCase());
    if (!lamp) return;

    lamp.classList.add('lamp-lit');
    this.currentActiveLamp = lamp;

    if (this.activeTimeout) clearTimeout(this.activeTimeout);
    this.activeTimeout = window.setTimeout(() => {
      this.clearLamp();
    }, 450); // Glow holds for ~450ms total
  }

  public clearLamp() {
    if (this.currentActiveLamp) {
      this.currentActiveLamp.classList.remove('lamp-lit');
      this.currentActiveLamp = null;
    }
  }
}
