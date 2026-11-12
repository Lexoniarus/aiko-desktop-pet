export const roomWalkAnimation = 'room-walk';

export const roomWalkClips = [
  'room-walk-away',
  'body-step-right-profil',
  'room-walk-toward',
  'body-step-left-profil',
] as const;

export type RoomWalkClip = (typeof roomWalkClips)[number];
export type RoomWalk = {
  clip: RoomWalkClip;
  distance: number;
  stepLength: number;
  stepDuration: number;
};

export function roomWalkFrame(
  clip: { duration: number; order: number[]; frames: Array<{ duration: number }> },
  walk: RoomWalk,
): number {
  const order = clip.order.length
    ? clip.order
    : clip.frames.map((_frame, index) => index);
  const stepsPerCycle = walk.clip.startsWith('room-walk-') ? 2 : 1;
  const cycleTime = walk.stepDuration * stepsPerCycle;
  const walkedTime = (walk.distance / walk.stepLength) * walk.stepDuration;
  // Map the physical cycle to the timing of the authored frames.
  let elapsed = ((walkedTime % cycleTime) / cycleTime) * clip.duration * 1000;
  for (const index of order) {
    elapsed -= clip.frames[index]!.duration;
    if (elapsed < 0) return index;
  }
  return order[0]!;
}
