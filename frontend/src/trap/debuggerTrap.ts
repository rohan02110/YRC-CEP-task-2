/**
 * Multi-Layer Debugger Trap & Tamper Detection
 * 1. Main-thread jittered debugger loop with delta timing
 * 2. Dedicated Web Worker debugger watchdog
 * 3. Console getter probe
 * 4. Window geometry heuristics & native code integrity checks
 */

import { api } from '../net/client';

let isTriggered = false;

function triggerViolationScreen(detector: string, evidence?: unknown) {
  if (isTriggered) return;
  isTriggered = true;

  // 1. Dispatch tamper beacon
  api.sendTamperBeacon(detector, evidence);

  // 2. Wipe application DOM
  document.body.innerHTML = `
    <div style="
      position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
      background: #0A0908; color: #C8892B; display: flex; flex-direction: column;
      align-items: center; justify-content: center; font-family: sans-serif;
      text-align: center; padding: 2rem; z-index: 9999999;
    ">
      <div style="font-size: 5rem; margin-bottom: 1.5rem; color: #7A1E1E;">⚔️</div>
      <h1 style="font-size: 2.2rem; color: #EADBB6; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 2px;">
        Dharma Has Been Violated
      </h1>
      <p style="font-size: 1.2rem; max-width: 600px; line-height: 1.6; color: #C8892B; margin-bottom: 2rem;">
        The sacred formation detects mortal instruments probing its wheels.<br>
        Abhimanyu's path is sealed. Your session has been revoked by Drona.
      </p>
      <div style="
        background: #141210; border: 1px solid #7A1E1E; padding: 1rem 2rem;
        border-radius: 4px; color: #7A1E1E; font-size: 0.95rem; font-family: monospace;
      ">
        VIOLATION CODE: ${detector.toUpperCase()}
      </div>
    </div>
  `;
}

export function initDebuggerTrap() {
  // 1. Main-Thread Jittered Debugger Loop with Timing Check
  (() => {
    const a = () => { debugger; };
    const b = () => { debugger; };
    const c = () => { debugger; };

    const tick = () => {
      const t0 = performance.now();
      a(); b(); c();
      const elapsed = performance.now() - t0;

      if (elapsed > 120 && document.visibilityState === 'visible') {
        triggerViolationScreen('dbg_main_timing', { elapsed });
      }
      setTimeout(tick, 15 + Math.random() * 35);
    };
    setTimeout(tick, 100);
  })();

  // 2. Web Worker Watchdog
  try {
    const workerBlob = new Blob([`
      (() => {
        const tick = () => { debugger; setTimeout(tick, 30 + Math.random() * 50); };
        tick();
        self.onmessage = (e) => { if (e.data === 'ping') self.postMessage('pong'); };
      })();
    `], { type: 'application/javascript' });

    const workerUrl = URL.createObjectURL(workerBlob);
    const worker = new Worker(workerUrl);
    let missedReplies = 0;
    let awaitingPong = false;
    let workerVerified = false;

    worker.onmessage = (e) => {
      if (e.data === 'pong') {
        workerVerified = true;
        awaitingPong = false;
        missedReplies = 0;
      }
    };

    worker.onerror = () => {
      // If browser sandboxing prevents blob workers, do not false-positive
    };

    // Give 2.5s startup grace period for worker initialization
    setTimeout(() => {
      setInterval(() => {
        if (awaitingPong && workerVerified && document.visibilityState === 'visible') {
          missedReplies++;
          if (missedReplies >= 4) {
            triggerViolationScreen('dbg_worker_paused', { missed: missedReplies });
          }
        }
        awaitingPong = true;
        worker.postMessage('ping');
      }, 500);
    }, 2500);
  } catch {
    // Workers might be restricted in some strict envs
  }

  // 3. Console Probe (Object Getter Evaluation)
  (() => {
    const probeObj = {};
    let probeHit = false;

    Object.defineProperty(probeObj, 'id', {
      get: () => {
        probeHit = true;
        triggerViolationScreen('dbg_console_probe', {});
        return 'chakra_core';
      },
      configurable: true
    });

    setInterval(() => {
      if (!probeHit) {
        // Logging probe object triggers getter ONLY when devtools console renders it
        console.debug(probeObj);
      }
    }, 1500);
  })();

  // 4. Environment Integrity & Window Delta Heuristics
  setInterval(() => {
    const deltaW = window.outerWidth - window.innerWidth;
    const deltaH = window.outerHeight - window.innerHeight;

    // Report heuristic as soft violation (requires corroboration on server)
    if ((deltaW > 160 || deltaH > 160) && document.visibilityState === 'visible') {
      api.reportSoftViolation('window_delta_heuristic', { deltaW, deltaH });
    }

    // Native Function integrity check
    if (typeof fetch !== 'function' || !fetch.toString().includes('[native code]')) {
      triggerViolationScreen('function_override_detected', { target: 'fetch' });
    }
  }, 2000);
}
