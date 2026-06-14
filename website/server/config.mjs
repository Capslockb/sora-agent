import express from 'express';
const app = express();
app.get('/api/health', (req, res) => res.json({ok: true}));
app.listen(3001, () => console.log('listening on 3099'));
console.log('started');
