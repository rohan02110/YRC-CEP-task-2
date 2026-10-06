/**
 * Client Lockdown & Shortcut Interception
 * Strict capture-phase non-passive event blockers, clipboard poisoning, and violation reporter.
 */

import { ALPHABET } from '../machine/types';
import { api } from '../net/client';

const DECOY_CLIPBOARD_FLAG = "KCTF{ABHIMANYU_NEVER_LEARNED_TO_EXIT}";

export function initClientLockdown(onValidMachineKey?: (char: string) => void) {
  // 1. Keyboard event interceptor
  const handleKeyDown = (e: KeyboardEvent) => {
    const activeEl = document.activeElement;
    const isTextInput = !!(activeEl && (
      activeEl.tagName === 'INPUT' ||
      activeEl.tagName === 'TEXTAREA' ||
      activeEl.tagName === 'SELECT' ||
      (activeEl as HTMLElement).isContentEditable
    ));

    // If typing in any input field (flag input, gate inputs, dials, etc.)
    if (isTextInput) {
      // Allow standard editing shortcuts (Ctrl/Cmd + A, C, V, X, Z)
      const isEditingCombo = (e.ctrlKey || e.metaKey) && ['a', 'c', 'v', 'x', 'z', 'A', 'C', 'V', 'X', 'Z'].includes(e.key);
      if (isEditingCombo) {
        return true;
      }

      // Block dangerous devtools/browser inspection shortcuts (e.g. F12, Ctrl+U, Ctrl+S, Ctrl+Shift+I)
      if (/^F([1-9]|1[0-2])$/.test(e.key)) {
        e.preventDefault();
        e.stopImmediatePropagation();
        api.reportSoftViolation('blocked_function_key', { key: e.key });
        return false;
      }

      if ((e.ctrlKey || e.metaKey) && !isEditingCombo) {
        e.preventDefault();
        e.stopImmediatePropagation();
        api.reportSoftViolation('blocked_ctrl_alt_combo', { key: e.key, code: e.code, ctrl: e.ctrlKey, meta: e.metaKey });
        return false;
      }

      // Allow all normal typing, spaces, symbols, and navigation keys inside input
      const allowedNav = ['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'Enter', 'Tab', 'Escape'];
      if (allowedNav.includes(e.key) || e.key.length === 1) {
        return true;
      }

      return true;
    }

    const hasCtrl = e.ctrlKey || e.metaKey;
    const hasAlt = e.altKey && !e.getModifierState('AltGraph');

    // Block any Ctrl/Meta or standard Alt combo on main page
    if (hasCtrl || hasAlt) {
      e.preventDefault();
      e.stopImmediatePropagation();
      api.reportSoftViolation('blocked_ctrl_alt_combo', { key: e.key, code: e.code, ctrl: e.ctrlKey, meta: e.metaKey, alt: e.altKey });
      return false;
    }

    // Block Function keys F1 - F12
    if (/^F([1-9]|1[0-2])$/.test(e.key)) {
      e.preventDefault();
      e.stopImmediatePropagation();
      api.reportSoftViolation('blocked_function_key', { key: e.key });
      return false;
    }

    // Machine Keyboard handling (only when NOT in an input field)
    // Ignore repeat key events (holding a key does not step multiple times)
    if (e.repeat) {
      e.preventDefault();
      e.stopImmediatePropagation();
      return false;
    }

    // Check if key is in 30-symbol alphabet
    let char = e.key.toUpperCase();
    // Allow space to map to underscore '_'
    if (e.key === ' ') char = '_';

    if (ALPHABET.includes(char)) {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (onValidMachineKey) {
        onValidMachineKey(char);
      }
      return false;
    }

    // Block any other key on machine
    e.preventDefault();
    e.stopImmediatePropagation();
    if (e.key !== 'Shift' && e.key !== 'AltGraph') {
      api.reportSoftViolation('blocked_unauthorized_key', { key: e.key, code: e.code });
    }
    return false;
  };

  // Register capture-phase listeners on window and document
  window.addEventListener('keydown', handleKeyDown, { capture: true, passive: false });
  document.addEventListener('keydown', handleKeyDown, { capture: true, passive: false });

  // 2. Clipboard Poisoning & Blocking (exempt input fields)
  const poisonClipboard = (e: ClipboardEvent) => {
    const target = e.target as HTMLElement | null;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
      return true;
    }
    e.preventDefault();
    e.stopImmediatePropagation();
    if (e.clipboardData) {
      e.clipboardData.setData('text/plain', DECOY_CLIPBOARD_FLAG);
    }
    api.reportSoftViolation('clipboard_poison_triggered', { type: e.type });
    return false;
  };

  const blockPaste = (e: ClipboardEvent) => {
    const target = e.target as HTMLElement | null;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
      return true;
    }
    e.preventDefault();
    e.stopImmediatePropagation();
    api.reportSoftViolation('paste_blocked', {});
    return false;
  };

  window.addEventListener('copy', poisonClipboard, { capture: true, passive: false });
  document.addEventListener('copy', poisonClipboard, { capture: true, passive: false });
  window.addEventListener('cut', poisonClipboard, { capture: true, passive: false });
  document.addEventListener('cut', poisonClipboard, { capture: true, passive: false });
  window.addEventListener('paste', blockPaste, { capture: true, passive: false });
  document.addEventListener('paste', blockPaste, { capture: true, passive: false });

  // 3. Block Context Menu, Drag, Selection, Print, Middle/Right clicks (exempt input fields)
  const blockDefault = (e: Event) => {
    const target = e.target as HTMLElement | null;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT')) {
      return true;
    }
    e.preventDefault();
    e.stopImmediatePropagation();
    if (e.type !== 'selectstart') {
      api.reportSoftViolation(`blocked_${e.type}`, {});
    }
    return false;
  };

  window.addEventListener('contextmenu', blockDefault, { capture: true, passive: false });
  document.addEventListener('contextmenu', blockDefault, { capture: true, passive: false });
  window.addEventListener('selectstart', blockDefault, { capture: true, passive: false });
  document.addEventListener('selectstart', blockDefault, { capture: true, passive: false });
  window.addEventListener('dragstart', blockDefault, { capture: true, passive: false });
  window.addEventListener('drop', blockDefault, { capture: true, passive: false });
  window.addEventListener('dragover', blockDefault, { capture: true, passive: false });
  window.addEventListener('beforeprint', blockDefault, { capture: true, passive: false });
  window.addEventListener('afterprint', blockDefault, { capture: true, passive: false });
  window.addEventListener('auxclick', blockDefault, { capture: true, passive: false });
}
