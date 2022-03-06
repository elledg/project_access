const WebSocket = require('ws');
const port = 7071;
const wss = new WebSocket.Server({ port: port });
const clients = new Map();

const fs = require('fs');
const log = "sftp.log";

console.log("sftp server listening on %d", port)
console.log("websocket server created")

function addToLog(data) {
    var time = (new Date()).toISOString().replace(/-/g, "/").replace(/T|Z/g, " ");
    var text = time + ' - ' + data;
  
      fs.appendFile(log, text, function (err) {
          if (err) throw err;
          console.log('Added to Log!');
      });
  }


wss.on('connection', (ws) => {
    message = 'received';
    const metadata = { message };

    clients.set(ws, metadata);
    ws.on('message', (messageAsString) => {
        console.log(messageAsString);
        const message = JSON.parse(messageAsString);
        const metadata = clients.get(ws);
        
        addToLog(messageAsString);

        message.status = metadata.message;
        const outbound = JSON.stringify(message);

        [...clients.keys()].forEach((client) => {
          client.send(outbound);
        });
      });

      ws.on("close", () => {
        clients.delete(ws);
      });
  });