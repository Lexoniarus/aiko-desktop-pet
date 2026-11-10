/** Cancel browser selection/menus/dragging without intercepting room gestures. */
export function protectRoomInteractions(host: HTMLElement): () => void {
  const controller = new AbortController();
  const blockNativeInteraction = (event: Event): void => {
    const target =
      event.target instanceof Element
        ? event.target
        : event.target instanceof Node
          ? event.target.parentElement
          : null;
    if (
      target?.closest('input, textarea, select') ||
      (target instanceof HTMLElement && target.isContentEditable)
    )
      return;
    event.preventDefault();
  };
  for (const type of ['selectstart', 'contextmenu', 'dragstart'])
    host.addEventListener(type, blockNativeInteraction, {
      capture: true,
      signal: controller.signal,
    });
  return () => controller.abort();
}
