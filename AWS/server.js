console.log('Server-side code running');

const express = require('express');
const app = express();
app.use(express.static('public'));

const http = require('http');
const WebSocket = require('ws');

const port = 8080;
const server = http.createServer(express);
const wss = new WebSocket.Server({ server })

// const MongoClient = require('mongodb').MongoClient;
// const url = "mongodb+srv://rome:Sug4rD4ddy@cluster0.4p3ah.mongodb.net/project?retryWrites=true&w=majority";
// let db;
// let data;

// MongoClient.connect(url, (err, database) => {
//   if(err) {
//     return console.log(err);
//   }
//   const collection = database.db("project").collection("access");

//   collection.find({}).toArray(function(err, result) {
//     if (err) throw err;
//     data = result.toString();
//     console.log(result);
//     database.close();
//   });

// index = 0;

  server.listen(port, function() {
    console.log('Server is listening on port ' + port + '!')
  })

  wss.on('connection', function connection(ws) {
    console.log('Client connected!');
    ws.send('Server connection established!');

    ws.on('message', function incoming(message) {
      console.log('Client says: %s', message);

      target_data = "(10,10);(0,0);1:00;2:00"
      wss.clients.forEach(function each(client) {
        if (client !== ws && client.readyState === WebSocket.OPEN) {
          client.send(target_data);
        }
      });
    });
  });
// });