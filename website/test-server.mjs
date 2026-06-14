import express from 'express';
const app = express();
app.get('/api/health', (req, res) => res.json({ok: true, express: '5.2.1'}));
const server = app.listen(3099, () => {
  console.log('listening on', server.address().port);
});
console.log('server created, event loop should stay alive');
