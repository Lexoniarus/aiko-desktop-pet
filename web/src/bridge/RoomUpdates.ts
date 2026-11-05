export interface UpdateState {
  installedVersion: string;
  availableVersion?: string;
  phase:
    'idle' | 'checking' | 'downloading' | 'ready' | 'current' | 'error' | 'applying';
  message: string;
  canRestart: boolean;
}

export interface RoomUpdates {
  subscribe(listener: (state: UpdateState) => void): () => void;
  check(): Promise<void>;
  apply(): Promise<void>;
}

export interface RoomHostOptions {
  updates: RoomUpdates;
  registerShutdown(shutdown: () => Promise<void>): void;
  setGameOpen(open: boolean): void;
}
