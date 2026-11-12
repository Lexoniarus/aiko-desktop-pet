export const roomWalkAnimation = 'room-walk';

export const roomWalkClips = [
  'room-walk-away',
  'body-step-right-profil',
  'room-walk-toward',
  'body-step-left-profil',
] as const;

const quarterTurn = Math.PI / 2;
const facingMargin = Math.PI / 36;

export class RoomWalkPresentation {
  private heading?: number;
  private facing?: number;

  clip(heading: number, bearing: number): (typeof roomWalkClips)[number] {
    const relative = heading - bearing;
    if (this.heading === heading && this.facing !== undefined) {
      const offset = relative - this.facing * quarterTurn;
      const angle = Math.atan2(Math.sin(offset), Math.cos(offset));
      if (Math.abs(angle) <= quarterTurn / 2 + facingMargin)
        return roomWalkClips[this.facing]!;
    }
    const turn = Math.round(relative / quarterTurn);
    this.heading = heading;
    this.facing = ((turn % 4) + 4) % 4;
    return roomWalkClips[this.facing]!;
  }

  reset(): void {
    this.heading = this.facing = undefined;
  }
}
