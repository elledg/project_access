const ws_port = 8000

const WebSocket = require('ws');
const wss_web = new WebSocket.Server({ port: ws_port });

const MongoClient = require('mongodb').MongoClient;

const { dir, MongoURL, database, addToDatabase, removeFromDatabase, addToLog, fileExists } = require("./lib");

console.log("WebSocket Server Listening on %d", ws_port)
start_ws()
function start_ws(){
	wss_web.on("connection", function(ws) {

		var id = setInterval(function() {
			MongoClient.connect(MongoURL, (err, client) => {
				if (err) return console.log(err);

				const db = client.db(database);
				console.log(`MongoDB Connected: ${MongoURL}`);
				
				const col = db.collection('requests');
				col.find().toArray((err, results) => {
					console.log(results);
					client.close();

					var data = {data:results}
					console.log(data)
					ws.send(JSON.stringify(data), function() {  });
					addToLog(data.data, 'logs_ws');

				});
			});   
		}, 1000)

		console.log("websocket connection open")

		ws.on("close", function() {
			console.log("websocket connection close")
			clearInterval(id)
		})
	})
}

module.exports =  start_ws ;