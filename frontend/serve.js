const http = require('http');
const fs = require('fs');
const path = require('path');
const port = 8080;

const mimeTypes = {
  '.html': 'text/html',
  '.js':   'application/javascript',
  '.css':  'text/css',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.svg':  'image/svg+xml',
  '.json': 'application/json'
};

const server = http.createServer((req, res) => {
  // Resolve file path relative to the frontend folder
  let filePath = path.join(__dirname, req.url);
  if (filePath.endsWith('/') || filePath === __dirname) {
    filePath = path.join(filePath, 'index.html');
  }
  const ext = path.extname(filePath).toLowerCase();
  const contentType = mimeTypes[ext] || 'application/octet-stream';
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not found');
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(data);
    }
  });
});

server.listen(port, () => {
  console.log(`Static server running at http://localhost:${port}`);
});
