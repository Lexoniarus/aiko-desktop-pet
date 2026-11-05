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
  node.addEventListener('click', action);
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
