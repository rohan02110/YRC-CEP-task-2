/**
 * Dedicated Web Worker Debugger Trap (w.ts)
 * Operates in separate thread; executes jittered debugger loop and responds to pings.
 */

(() => {
  const tickWorker = () => {
    debugger;
    setTimeout(tickWorker, 30 + Math.random() * 50);
  };
  tickWorker();

  self.onmessage = (e: MessageEvent) => {
    if (e.data === 'ping') {
      self.postMessage('pong');
    }
  };
})();
