/**
 * The Chakravyuha Cipher - Frontend Core Entrypoint (v2 Hardened)
 * Enclosed in an isolated module closure with prototype freezing and zero window leaks.
 */

import { api } from './net/client';
import { sound } from './audio/synth';
import { initDebuggerTrap } from './trap/debuggerTrap';
import { initClientLockdown } from './lockdown/shortcuts';
import { initFullscreenGate } from './ui/fullscreen';

import { RotorDisplay } from './machine/rotors';
import { Lampboard } from './machine/lampboard';
import { Keyboard } from './machine/keyboard';
import { OutputTape } from './machine/tape';
import { MachineControls } from './machine/controls';
import { GaugeDisplay } from './machine/gauge';
import { ArtifactsModal } from './ui/artifactsModal';
import { CodexModal } from './ui/codexModal';
import { GatesPanel } from './ui/gates';

(() => {
  // 1. Prototype Freezing & Tamper Hardening
  try {
    Object.freeze(Object.prototype);
    Object.freeze(Array.prototype);
    Object.freeze(Function.prototype);
  } catch {
    // If strict environment restricts prototype freeze
  }

  // 2. Initialize Debugger Trap & Client Lockdown
  initDebuggerTrap();

  // Spiral rotation state
  let chakraRotation = 0;

  // Mount components
  const gaugeMount = document.getElementById('gauge-mount');
  const rotorsMount = document.getElementById('rotors-mount');
  const lampMount = document.getElementById('lampboard-mount');
  const keyMount = document.getElementById('keyboard-mount');
  const ctrlMount = document.getElementById('controls-mount');
  const artMount = document.getElementById('artifacts-mount');
  const gatesMount = document.getElementById('gates-mount');
  const tapeCanvas = document.getElementById('output-tape-canvas') as HTMLCanvasElement;
  const modeLabel = document.getElementById('mmi-mode-label');

  if (!gaugeMount || !rotorsMount || !lampMount || !keyMount || !ctrlMount || !artMount || !tapeCanvas) {
    console.error('DOM mounting nodes missing');
    return;
  }

  const gauge = new GaugeDisplay(gaugeMount);
  const rotors = new RotorDisplay(rotorsMount);
  const lampboard = new Lampboard(lampMount);
  const tape = new OutputTape(tapeCanvas);
  const artifactsModal = new ArtifactsModal(artMount);

  // Controls Component
  const controls = new MachineControls(
    ctrlMount,
    async (walzenlage, rings, grund, plugboard) => {
      sound.playRelayThunk();
      await api.configureMachine(walzenlage, rings, grund, plugboard);
      rotors.setPositionsDirect(grund);
      tape.clear();
    },
    async () => {
      sound.playRelayThunk();
      await api.resetChakra();
      const st = api.getState();
      if (st) {
        rotors.setPositionsDirect(st.grundstellung);
      }
      tape.clear();
    }
  );

  // Gates Component
  if (gatesMount) {
    new GatesPanel(gatesMount, async () => {
      // Callback on mode switch to Original
      if (modeLabel) {
        modeLabel.textContent = 'ORIGINAL CELESTIAL ENGINE (COMMANDED BY YOUR ARMY)';
        modeLabel.style.color = '#E5A93C';
      }
      await artifactsModal.render();
    });
  }

  // Key Press Handler
  const handleMachineKeyPress = async (char: string) => {
    sound.playKeyClick();

    try {
      const res = await api.pressKey(char);

      // Advance rotating Chakravyuha SVG spiral 12° per key press
      chakraRotation += 12;
      document.documentElement.style.setProperty('--chakra-rot', `${chakraRotation}deg`);

      // Update rotor drum animations and positions
      rotors.updatePositions(res.positions, res.steppedFlags);

      // Play distinct ticks for rotors that stepped
      sound.playRotorTicks(res.steppedFlags);

      // Light output lamp on lampboard
      lampboard.lightLamp(res.outSymbol);

      // Append to canvas tape
      tape.appendSymbol(res.outSymbol);

      // Update controls sealing state
      controls.setSealed(res.isSealed);
    } catch (err: unknown) {
      console.warn((err as Error).message);
    }
  };

  const keyboard = new Keyboard(keyMount, handleMachineKeyPress);

  // Panels & Modals
  const codex = new CodexModal();

  // Codex Trigger Buttons
  const openCodexBtn = document.getElementById('open-codex-btn');
  if (openCodexBtn) {
    openCodexBtn.addEventListener('click', () => {
      codex.show('story');
    });
  }

  const expandCodexBtn = document.getElementById('briefing-expand-codex-btn');
  if (expandCodexBtn) {
    expandCodexBtn.addEventListener('click', () => {
      codex.show('workflow');
    });
  }

  const quickStepBtns = document.querySelectorAll('.quick-step-btn');
  quickStepBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      codex.show('workflow');
    });
  });

  // Mute Audio toggle
  const muteBtn = document.getElementById('mute-toggle-btn');
  if (muteBtn) {
    muteBtn.addEventListener('click', () => {
      const isMuted = sound.toggleMute();
      muteBtn.textContent = `MUTE AUDIO: ${isMuted ? 'ON' : 'OFF'}`;
    });
  }

  // State Change Listener
  api.setOnStateChange((st) => {
    gauge.updateStatus(
      st.baanRemaining,
      st.lifetimeCapRemaining,
      st.isLocked,
      st.lockRemainingSeconds,
      st.lockReason
    );
    keyboard.setEnabled(!st.isLocked && !st.isBanned);
    controls.setSealed(st.isSealed);
    if (st.mode === 'original' && modeLabel) {
      modeLabel.textContent = 'ORIGINAL CELESTIAL ENGINE (COMMANDED BY YOUR ARMY)';
      modeLabel.style.color = '#E5A93C';
    }
  });

  // Client Lockdown with physical keyboard mapping to handleMachineKeyPress
  initClientLockdown((char) => {
    keyboard.triggerKey(char);
  });

  // Fullscreen Gate
  initFullscreenGate();

  // Initialize Session
  api.initSession().then(async (st) => {
    rotors.setPositionsDirect(st.currentPositions);
    controls.updateState(st.walzenlage, st.ringstellung, st.grundstellung, st.plugboard, st.isSealed);
    await artifactsModal.render();
  }).catch((err) => {
    console.error('Session init error:', err);
  });
})();
