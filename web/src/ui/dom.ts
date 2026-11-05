import type { RoomCommandName } from '../bridge/commands';
export type Command = (
  name: RoomCommandName,
  args?: Record<string, unknown>,
) => Promise<void>;
export function element<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className = '',
  text = '',
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = text;
  return node;
}
export function button(text: string, action: () => void): HTMLButtonElement {
  const node = element('button', '', text);
  node.type = 'button';
  let touch: { id: number; x: number; y: number } | undefined;
  let lastInput = '';
  let activatedAt = -Infinity;
  node.addEventListener('pointerdown', (event) => {
    lastInput = event.pointerType;
    touch =
      event.isPrimary && event.pointerType === 'touch' && !node.disabled
        ? { id: event.pointerId, x: event.clientX, y: event.clientY }
        : undefined;
  });
  node.addEventListener('pointermove', (event) => {
    if (
      touch?.id === event.pointerId &&
      Math.hypot(event.clientX - touch.x, event.clientY - touch.y) > 8
    )
      touch = undefined;
  });
  node.addEventListener('pointercancel', () => {
    touch = undefined;
  });
  node.addEventListener('pointerup', (event) => {
    const tap = touch;
    touch = undefined;
    if (
      !tap ||
      tap.id !== event.pointerId ||
      node.disabled ||
      Math.hypot(event.clientX - tap.x, event.clientY - tap.y) > 8
    )
      return;
    if (
      document.elementFromPoint(event.clientX, event.clientY)?.closest('button') !==
      node
    )
      return;
    // A captured canvas drag can leave a browser without a compatibility click.
    // Admit one completed touch here; suppress only its later native duplicate.
    activatedAt = performance.now();
    node.click();
  });
  node.addEventListener('click', (event) => {
    if (
      event.isTrusted &&
      event.detail > 0 &&
      lastInput === 'touch' &&
      performance.now() - activatedAt < 700
    ) {
      event.preventDefault();
      event.stopImmediatePropagation();
      return;
    }
    if (!node.disabled) action();
  });
  return node;
}
export function line(text: string): HTMLParagraphElement {
  return element('p', '', text);
}
export function link(label: string, url: string): HTMLAnchorElement | HTMLSpanElement {
  if (!/^https:\/\//.test(url)) return element('span', '', label);
  const node = element('a', '', label);
  node.href = url;
  node.target = '_blank';
  node.rel = 'noopener noreferrer';
  return node;
}
