import assert from 'node:assert/strict';
import test from 'node:test';
import { readStorageStatus } from '../src/platforms/browser/DeviceReport.ts';

test('storage diagnostics distinguish refusal from missing browser support', async () => {
  assert.deepEqual(await readStorageStatus(), {
    persistenceSupported: false,
    persisted: null,
    estimateSupported: false,
    usageBytes: null,
    quotaBytes: null,
  });
  const storage = {
    persisted: async () => false,
    estimate: async () => ({ usage: 120, quota: 1024 }),
    persist: () => assert.fail('A diagnostic must not request persistence'),
  };
  assert.deepEqual(await readStorageStatus(storage), {
    persistenceSupported: true,
    persisted: false,
    estimateSupported: true,
    usageBytes: 120,
    quotaBytes: 1024,
  });
});

test('one rejected storage query does not hide the other diagnostic', async () => {
  const result = await readStorageStatus({
    persisted: async () => {
      throw new Error('Denied');
    },
    estimate: async () => ({ usage: 15 }),
  });
  assert.equal(result.persisted, null);
  assert.equal(result.persistenceSupported, true);
  assert.equal(result.usageBytes, 15);
  assert.equal(result.quotaBytes, null);
  const partial = await readStorageStatus({ persisted: async () => true });
  assert.equal(partial.persisted, true);
  assert.equal(partial.estimateSupported, false);
});
