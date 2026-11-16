import type { FurniturePlacement, RoomLayout } from './RoomLayout';
import { depthReferenceHeight } from './RoomDepthCurve.ts';
import { furnitureFrame, roomPresentation } from './RoomPresentation.ts';
import type { RoomProjection } from './RoomProjection';

/** Visible board contact measured down from the rear rim of the table sprite. */
export const artworkTabletopInset = 0.12;

const northWallArtwork = {
  wallHeight: 350,
  pixelsPerUnit: 2.2,
  doorHeight: 120.1725,
  fridgeHeight: 120.1725,
  kitchenHeight: 67,
  cupboardBottom: 194,
  cupboardWidth: 0.88,
} as const;

// Contact measurements from the approved furniture preview at the reference height.
const furnitureArtwork = {
  bedBelowSkirting: 74.44,
  stoolAheadOfDesk: 19.05,
  tableHeight: 92.26,
} as const;

export const artworkAttachments: Partial<
  Record<
    string,
    {
      asset: string;
      offsetX: number;
      offsetY?: number;
      wallOffset?: number;
      width: number;
    }
  >
> = {
  kitchen: {
    asset: 'kitchenUpper',
    offsetX: -0.04,
    wallOffset: northWallArtwork.cupboardBottom - northWallArtwork.wallHeight,
    width: northWallArtwork.cupboardWidth,
  },
  desk: { asset: 'laptop', offsetX: 0.17, offsetY: 0.14, width: 0.22 },
};

export function artworkWallScale(projection: RoomProjection) {
  return projection.floorLine / northWallArtwork.wallHeight;
}

export function artworkFurnitureFrame(
  projection: RoomProjection,
  item: FurniturePlacement,
) {
  const frame = furnitureFrame(projection, item);
  const referenceScale =
    (projection.fit * roomPresentation.designHeight) / depthReferenceHeight;
  switch (item.id) {
    case 'bed':
      return placeArtwork(
        frame,
        item,
        projection.floorBounds.top + furnitureArtwork.bedBelowSkirting * referenceScale,
      );
    case 'stool': {
      const desk = projection.layout.furniture.find((entry) => entry.id === 'desk')!;
      const deskY = furnitureFrame(projection, desk).y;
      return placeArtwork(
        frame,
        item,
        deskY + furnitureArtwork.stoolAheadOfDesk * referenceScale,
      );
    }
    case 'table':
      return placeArtwork(
        frame,
        item,
        frame.y,
        furnitureArtwork.tableHeight * referenceScale,
      );
  }
  if (item.id !== 'door' && (!item.wall || !item.elevation)) return frame;
  // The mounted art retains its drawing scale independently of the floor.
  const wallScale =
    item.id === 'door'
      ? northWallArtwork.pixelsPerUnit * artworkWallScale(projection)
      : projection.angularScale / frame.surface.depth;
  const height = item.height * wallScale;
  const scale = height / item.crop[3];
  const y = item.elevation
    ? projection.yAt(Infinity) +
      (projection.layout.camera_height - item.elevation) * wallScale
    : projection.floorLine;
  return {
    ...frame,
    y,
    height,
    width: item.crop[2] * scale,
    scale,
  };
}

function placeArtwork(
  frame: ReturnType<typeof furnitureFrame>,
  item: FurniturePlacement,
  y: number,
  height = frame.height,
) {
  const scale = height / item.crop[3];
  return {
    ...frame,
    y,
    height,
    width: item.crop[2] * scale,
    scale,
    surface: { ...frame.surface, y: y - height, scale: height / item.height },
    order: item.wall ? frame.order : y,
  };
}

/** Art dimensions and decorative props; the simulation keeps its layout. */
export function artworkFurniture(
  layout: RoomLayout,
  images: Record<string, HTMLImageElement>,
): FurniturePlacement[] {
  const desk = layout.furniture.find((item) => item.id === 'desk')!;
  const furniture = layout.furniture.map((item) => {
    switch (item.id) {
      case 'door':
        return { ...item, height: northWallArtwork.doorHeight };
      case 'fridge':
        return { ...item, height: northWallArtwork.fridgeHeight };
      case 'kitchen':
        return { ...item, height: northWallArtwork.kitchenHeight };
      case 'desk':
        return { ...item, height: 57 };
      case 'plant':
        return { ...item, height: 52 };
      default:
        return item;
    }
  });
  furniture.push(
    {
      ...desk,
      id: 'stool',
      asset: 'stool',
      x: desk.x + desk.width / 2 + 70,
      z: desk.z + 10,
      height: 32,
      wall: null,
      blocking: false,
    },
    {
      ...desk,
      id: 'wallArt',
      asset: 'wallArt',
      x: 0,
      z: desk.z - 100,
      height: 48,
      elevation: 109,
      blocking: false,
    },
  );
  return furniture.map((item) => {
    const image = images[item.asset]!;
    return { ...item, crop: [0, 0, image.naturalWidth, image.naturalHeight] };
  });
}
