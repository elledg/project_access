const WebSocket = require('ws');
const port = 7071;
const wss = new WebSocket.Server({ port: port });
const clients = new Map();

const fs = require('fs');
const log = "sftp.log";
const dir = '/var/sftp/myfolder/data/';

console.log("sftp server listening on %d", port)
console.log("websocket server created")

function fileExists(trafficID){
    // list all files in the directory
    try {
        const files = fs.readdirSync(dir);

        // files object contains all files names
        for (let i = 0; i < files.length; i++) {
            file = files[i];
            var name = file.split(".")[0]
            if (name == trafficID){
                console.log(trafficID + " found")
                return true
            }
        }
        return false
    } catch (err) {
        console.log(err);
    }
}

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
        
        if (fileExists(message.trafficID)) {
            addToLog(messageAsString);
            message.status = metadata.message;
        }

        const outbound = JSON.stringify(message);

        [...clients.keys()].forEach((client) => {
          client.send(outbound);
        });
      });

      ws.on("close", () => {
        clients.delete(ws);
      });
  });