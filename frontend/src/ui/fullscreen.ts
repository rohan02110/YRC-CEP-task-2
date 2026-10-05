/**
 * Fullscreen Gate & Viewport Size Guard
 * Covers the machine until fullscreen is active; exiting fullscreen re-covers without penalty.
 */

export function initFullscreenGate(onFullscreenChange?: (isFullscreen: boolean) => void) {
  const gateOverlay = document.getElementById('fullscreen-gate');
  const enterBtn = document.getElementById('enter-fullscreen-btn');
  const sizeGuard = document.getElementById('size-guard');

  // 1. Viewport size check (< 1100x700)
  const checkSize = () => {
    if (sizeGuard) {
      if (window.innerWidth < 1100 || window.innerHeight < 700) {
        sizeGuard.classList.remove('hidden');
      } else {
        sizeGuard.classList.add('hidden');
      }
    }
  };

  window.addEventListener('resize', checkSize);
  checkSize();

  // 2. Fullscreen toggle
  const updateFullscreenState = () => {
    const isFs = !!document.fullscreenElement;
    if (gateOverlay) {
      if (isFs) {
        gateOverlay.classList.add('hidden');
      } else {
        gateOverlay.classList.remove('hidden');
      }
    }

    // Try keyboard lock if supported
    const nav = navigator as unknown as { keyboard?: { lock?: () => Promise<void> } };
    if (isFs && nav.keyboard && typeof nav.keyboard.lock === 'function') {
      nav.keyboard.lock().catch(() => {});
    }

    if (onFullscreenChange) {
      onFullscreenChange(isFs);
    }
  };

  document.addEventListener('fullscreenchange', updateFullscreenState);

  if (enterBtn) {
    enterBtn.addEventListener('click', async () => {
      try {
        if (!document.fullscreenElement) {
          await document.documentElement.requestFullscreen();
        }
      } catch {
        // Fallback if browser blocks fullscreen
        if (gateOverlay) gateOverlay.classList.add('hidden');
      }
    });
  }

  updateFullscreenState();
}
