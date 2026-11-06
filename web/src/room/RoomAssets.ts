export interface ItemStateAsset {
  file: string;
  pivot: [number, number];
  dimensions: [number, number];
  offset?: [number, number];
}
export interface RoomItemAsset extends ItemStateAsset {
  label: string;
  states?: Record<string, ItemStateAsset>;
  handOffset?: [number, number];
  worldZoom?: number;
  size?: number;
}
