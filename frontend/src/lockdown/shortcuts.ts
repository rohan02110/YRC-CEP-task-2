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

    // A. Detect and block all Copy / Paste / Cut keyboard shortcuts everywhere (both inside and outside inputs)
    const isPasteCombo =
      ((e.ctrlKey || e.metaKey) && (e.key === 'v' || e.key === 'V' || e.code === 'KeyV')) ||
      (e.shiftKey && (e.key === 'Insert' || e.code === 'Insert'));

    const isCopyCombo =
      ((e.ctrlKey || e.metaKey) && (e.key === 'c' || e.key === 'C' || e.code === 'KeyC')) ||
      ((e.ctrlKey || e.metaKey) && (e.key === 'Insert' || e.code === 'Insert'));

    const isCutCombo =
      ((e.ctrlKey || e.metaKey) && (e.key === 'x' || e.key === 'X' || e.code === 'KeyX')) ||
      (e.shiftKey && (e.key === 'Delete' || e.code === 'Delete' || e.key === 'Del'));

    if (isPasteCombo) {
      e.preventDefault();
      e.stopImmediatePropagation();
      api.reportSoftViolation('paste_blocked', { key: e.key, code: e.code });
      return false;
    }

    if (isCopyCombo || isCutCombo) {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(DECOY_CLIPBOARD_FLAG).catch(() => {});
      }
      api.reportSoftViolation('clipboard_poison_triggered', {
        key: e.key,
        code: e.code,
        action: isCopyCombo ? 'copy' : 'cut'
      });
      return false;
    }

    // B. Block Function keys F1 - F12 everywhere
    if (/^F([1-9]|1[0-2])$/.test(e.key)) {
      e.preventDefault();
      e.stopImmediatePropagation();
      api.reportSoftViolation('blocked_function_key', { key: e.key });
      return false;
    }

    // C. If typing in any input field (flag input, gate inputs, dials, etc.)
    if (isTextInput) {
      // Allow select all (Ctrl+A) and undo/redo (Ctrl+Z, Ctrl+Y)
      const isAllowedNavCombo = (e.ctrlKey || e.metaKey) && ['a', 'A', 'z', 'Z', 'y', 'Y'].includes(e.key);
      if (isAllowedNavCombo) {
        return true;
      }

      // Block any other Ctrl / Meta / Alt combos in input fields (e.g. Ctrl+S, Ctrl+U, Ctrl+Shift+I, etc.)
      if (e.ctrlKey || e.metaKey || (e.altKey && !e.getModifierState('AltGraph'))) {
        e.preventDefault();
        e.stopImmediatePropagation();
        api.reportSoftViolation('blocked_ctrl_alt_combo', { key: e.key, code: e.code, ctrl: e.ctrlKey, meta: e.metaKey, alt: e.altKey });
        return false;
      }

      // Allow all normal typing, spaces, symbols, and navigation keys inside input
      const allowedNav = ['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'Enter', 'Tab', 'Escape'];
      if (allowedNav.includes(e.key) || e.key.length === 1) {
        return true;
      }

      return true;
    }

    // D. Machine Keyboard handling (only when NOT in an input field)
    const hasCtrl = e.ctrlKey || e.metaKey;
    const hasAlt = e.altKey && !e.getModifierState('AltGraph');

    // Block any Ctrl/Meta or standard Alt combo on main page
    if (hasCtrl || hasAlt) {
      e.preventDefault();
      e.stopImmediatePropagation();
      api.reportSoftViolation('blocked_ctrl_alt_combo', { key: e.key, code: e.code, ctrl: e.ctrlKey, meta: e.metaKey, alt: e.altKey });
      return false;
    }

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

  // Register capture-phase keydown listeners on window and document
  window.addEventListener('keydown', handleKeyDown, { capture: true, passive: false });
  document.addEventListener('keydown', handleKeyDown, { capture: true, passive: false });

  // 2. Universal Clipboard Poisoning & Blocking (NO input exemption)
  const poisonClipboard = (e: ClipboardEvent) => {
    e.preventDefault();
    e.stopImmediatePropagation();
    if (e.clipboardData) {
      e.clipboardData.setData('text/plain', DECOY_CLIPBOARD_FLAG);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(DECOY_CLIPBOARD_FLAG).catch(() => {});
    }
    api.reportSoftViolation('clipboard_poison_triggered', { type: e.type });
    return false;
  };

  const blockPaste = (e: ClipboardEvent) => {
    e.preventDefault();
    e.stopImmediatePropagation();
    api.reportSoftViolation('paste_blocked', {});
    return false;
  };

  // Intercept beforeinput paste and drop events (modern browsers/mobile autofill)
  const handleBeforeInput = (e: InputEvent) => {
    if (e.inputType === 'insertFromPaste' || e.inputType === 'insertFromDrop') {
      e.preventDefault();
      e.stopImmediatePropagation();
      api.reportSoftViolation('paste_blocked', { inputType: e.inputType });
      return false;
    }
  };

  window.addEventListener('copy', poisonClipboard, { capture: true, passive: false });
  document.addEventListener('copy', poisonClipboard, { capture: true, passive: false });
  window.addEventListener('cut', poisonClipboard, { capture: true, passive: false });
  document.addEventListener('cut', poisonClipboard, { capture: true, passive: false });
  window.addEventListener('paste', blockPaste, { capture: true, passive: false });
  document.addEventListener('paste', blockPaste, { capture: true, passive: false });
  window.addEventListener('beforeinput', handleBeforeInput as EventListener, { capture: true, passive: false });
  document.addEventListener('beforeinput', handleBeforeInput as EventListener, { capture: true, passive: false });

  // 3. Block Context Menu, Drag & Drop, Selection, Print, Middle/Right clicks
  const blockContextMenu = (e: MouseEvent) => {
    e.preventDefault();
    e.stopImmediatePropagation();
    api.reportSoftViolation('blocked_contextmenu', {});
    return false;
  };

  const blockDragDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopImmediatePropagation();
    if (e.type === 'drop') {
      api.reportSoftViolation('blocked_drop', {});
    }
    return false;
  };

  const blockAuxClick = (e: MouseEvent) => {
    // Middle click (button === 1) or secondary click (button === 2)
    if (e.button === 1 || e.button === 2) {
      e.preventDefault();
      e.stopImmediatePropagation();
      api.reportSoftViolation('blocked_auxclick', { button: e.button });
      return false;
    }
  };

  const handleSelectStart = (e: Event) => {
    const target = e.target as HTMLElement | null;
    // Allow text selection inside inputs for cursor placement and editing
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
      return true;
    }
    e.preventDefault();
    e.stopImmediatePropagation();
    return false;
  };

  const blockPrint = (e: Event) => {
    e.preventDefault();
    e.stopImmediatePropagation();
    api.reportSoftViolation(`blocked_${e.type}`, {});
    return false;
  };

  window.addEventListener('contextmenu', blockContextMenu, { capture: true, passive: false });
  document.addEventListener('contextmenu', blockContextMenu, { capture: true, passive: false });
  window.addEventListener('dragstart', blockDragDrop, { capture: true, passive: false });
  document.addEventListener('dragstart', blockDragDrop, { capture: true, passive: false });
  window.addEventListener('dragover', blockDragDrop, { capture: true, passive: false });
  document.addEventListener('dragover', blockDragDrop, { capture: true, passive: false });
  window.addEventListener('drop', blockDragDrop, { capture: true, passive: false });
  document.addEventListener('drop', blockDragDrop, { capture: true, passive: false });
  window.addEventListener('selectstart', handleSelectStart, { capture: true, passive: false });
  document.addEventListener('selectstart', handleSelectStart, { capture: true, passive: false });
  window.addEventListener('beforeprint', blockPrint, { capture: true, passive: false });
  document.addEventListener('beforeprint', blockPrint, { capture: true, passive: false });
  window.addEventListener('afterprint', blockPrint, { capture: true, passive: false });
  document.addEventListener('afterprint', blockPrint, { capture: true, passive: false });
  window.addEventListener('auxclick', blockAuxClick, { capture: true, passive: false });
  document.addEventListener('auxclick', blockAuxClick, { capture: true, passive: false });
}
