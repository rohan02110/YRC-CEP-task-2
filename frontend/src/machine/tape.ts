/**
 * Mechanical Paper Output Tape (Rendered to <canvas>)
 * Non-selectable, groups of 5 symbols with perforated parchment visual styling.
 */

export class OutputTape {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private symbols: string[] = [];

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d') as CanvasRenderingContext2D;
    this.initCanvas();
  }

  private initCanvas() {
    this.canvas.width = 900;
    this.canvas.height = 48;
    this.draw();
  }

  public appendSymbol(char: string) {
    this.symbols.push(char);
    this.draw();
  }

  public clear() {
    this.symbols = [];
    this.draw();
  }

  public draw() {
    const { ctx, canvas } = this;
    const w = canvas.width;
    const h = canvas.height;

    // Background parchment strip
    ctx.fillStyle = '#EADBB6';
    ctx.fillRect(0, 0, w, h);

    // Subtle edge borders
    ctx.strokeStyle = '#C4B087';
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, w - 2, h - 2);

    // Format text into groups of 5
    const text = this.symbols.join('');
    const groups: string[] = [];
    for (let i = 0; i < text.length; i += 5) {
      groups.push(text.slice(i, i + 5));
    }
    const formatted = groups.join('  ');

    // Font settings
    ctx.fillStyle = '#1B140B';
    ctx.font = 'bold 20px monospace';
    ctx.textBaseline = 'middle';

    // Measure text width to right-align and scroll when long
    const textMetrics = ctx.measureText(formatted);
    let startX = 20;
    if (textMetrics.width > w - 40) {
      startX = w - 20 - textMetrics.width;
    }

    ctx.fillText(formatted, startX, h / 2);
  }
}
