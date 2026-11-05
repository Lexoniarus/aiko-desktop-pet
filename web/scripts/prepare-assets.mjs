import { execFileSync } from 'node:child_process';
execFileSync(process.env.AIKO_PYTHON ?? 'python', ['../scripts/export_room_icons.py'], { stdio: 'inherit' });
