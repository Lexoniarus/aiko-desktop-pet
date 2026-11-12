export const roomWalkAnimation = 'room-walk';

export const roomWalkClips = [
  'room-walk-away',
  'body-step-right-profil',
  'room-walk-toward',
  'body-step-left-profil',
] as const;

export type RoomWalkClip = (typeof roomWalkClips)[number];

export function roomWalkFrame(
  clip: { duration: number; order: number[]; frames: Array<{ duration: number }> },
  distance: number,
  stepLength: number,
): number {
  const order = clip.order.length
    ? clip.order
    : clip.frames.map((_frame, index) => index);
  let elapsed = ((distance / stepLength) * 620) % (clip.duration * 1000);
  for (const index of order) {
    elapsed -= clip.frames[index]!.duration;
    if (elapsed < 0) return index;
  }
  return order[0]!;
}
