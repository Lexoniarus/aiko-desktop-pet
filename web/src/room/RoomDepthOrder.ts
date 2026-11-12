/** Ground items cover an actor at effectively the same projected floor depth. */
export function objectGroundOrder(objectGroundY: number): number {
  return objectGroundY + 0.001;
}
