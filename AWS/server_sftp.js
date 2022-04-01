const sftp_port = 7071

const WebSocket = require('ws');
const wss_sftp = new WebSocket.Server({ port: sftp_port });
const clients = new Map();

const { dir, MongoURL, database, addToDatabase, removeFromDatabase, addToLog, fileExists } = require("./lib");


console.log("SFTP Server Listening on %d", sftp_port)
start_sftp()
function start_sftp(){
    wss_sftp.on('connection', (ws) => {
    message = 'received';
    const metadata = { message };

    clients.set(ws, metadata);
    ws.on('message', (messageAsString) => {
        console.log(messageAsString);
        const message = JSON.parse(messageAsString);
        const metadata = clients.get(ws);
        console.log("Recieved ", message.trafficID)
        message.status = metadata.message;
        if (fileExists(message.trafficID)) {
            addToLog(message, 'logs_sftp');
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
}

module.exports =  start_sftp ;
