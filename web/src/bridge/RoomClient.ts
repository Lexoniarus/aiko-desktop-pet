export interface RoomReply {
  protocol: 1; requestId: number; ok: boolean;
  snapshot?: RoomSnapshot; error?: string; saved?: boolean;
}
export interface RoomSnapshot {
  revision: number;
  pet: Record<string, unknown>;
  room: { pet: { x: number; depth: number }; object_depths: [string, number][] };
  objects: Array<{ instance_id: string; definition_id: string; revision: number; state: string; position: { x: number; height: number } | null }>;
  speech: { text: string; emote: string; id: number; active: boolean; story: boolean };
  animation: string;
  animation_id: number;
  held_item?: string | null;
  held_pose?: string;
  moving: boolean;
  facing: number;
  game: Record<string, unknown> | null;
  catalog: Record<string, unknown>;
  social?: unknown;
  error: string | null;
}
export interface RoomClient {
  command(name: string, args?: Record<string, unknown>): Promise<RoomReply>;
  close(): Promise<void>;
}
