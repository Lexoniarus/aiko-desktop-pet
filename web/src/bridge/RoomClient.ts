import type { RoomCommandName } from './commands';
export interface RoomReply {
  protocol: 2;
  requestId: number;
  ok: boolean;
  snapshot?: RoomSnapshot;
  error?: string;
  saved?: boolean;
  runtime?: Record<string, string>;
}
export interface PlayerApproach {
  serial: number;
  entry: { x: number; depth: number };
  target: { x: number; depth: number };
  framing: number;
  active: boolean;
}
export interface RoomSnapshot {
  revision: number;
  pet: Record<string, unknown>;
  room: {
    pet: { x: number; depth: number };
    object_depths: [string, number][];
    geometry_version: 2;
    layout_id: string;
    layout_revision: number;
  };
  objects: Array<{
    instance_id: string;
    definition_id: string;
    revision: number;
    state: string;
    position: { x: number; height: number } | null;
  }>;
  speech: {
    text: string;
    emote: string;
    id: number;
    active: boolean;
    story: boolean;
    accent?: string;
  };
  drag?: { instance_id: string | null; ready: boolean };
  animation: string;
  animation_id: number;
  animation_timings?: number[] | null;
  animation_hold_frame?: number | null;
  held_item?: string | null;
  held_pose?: string;
  moving: boolean;
  player_approach?: PlayerApproach | null;
  heading: number;
  motion?: {
    serial: number;
    time: number;
    travelled: Array<{ x: number; depth: number }>;
  };
  facing: number;
  game: Record<string, unknown> | null;
  catalog: Record<string, unknown>;
  social?: unknown;
  error: string | null;
}
export interface RoomClient {
  command(name: RoomCommandName, args?: Record<string, unknown>): Promise<RoomReply>;
  close(): Promise<void>;
}
