export const roomWalkAnimation = 'room-walk';

export const roomWalkClips = [
  'room-walk-away',
  'body-step-right-profil',
  'room-walk-toward',
  'body-step-left-profil',
] as const;

const quarterTurn = Math.PI / 2;

export class RoomWalkPresentation {
  private heading?: number;
  private facing = 0;

  clip(heading: number, wallBearing: number): (typeof roomWalkClips)[number] {
    // A straight path uses one authored gait through the whole segment.
    if (this.heading !== heading) {
      this.heading = heading;
      const turn = Math.round((heading - wallBearing) / quarterTurn);
      this.facing = ((turn % 4) + 4) % 4;
    }
    return roomWalkClips[this.facing]!;
  }

  reset(): void {
    this.heading = undefined;
  }
}
