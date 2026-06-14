// Wrapper to keep Express server alive
import('./server/index.js').then(() => {
  console.log('[wrapper] Server module loaded, keeping alive...');
  // Keep the process alive
  process.stdin.resume();
}).catch(e => {
  console.error('[wrapper] Failed:', e);
  process.exit(1);
});
