var WebSocketServer = require("ws").Server
var http = require("http")
var express = require("express")
var app = express()
var port = process.env.PORT || 8080

const fs = require('fs');
const log = "http.log";

app.use(express.static(__dirname + "/"))

var server = http.createServer(app)
server.listen(port)

console.log("http server listening on %d", port)

var wss = new WebSocketServer({server: server})
console.log("websocket server created")

function addToLog(data) {
  var time = (new Date()).toISOString().replace(/-/g, "/").replace(/T|Z/g, " ");
  var text = time + ' - ' + data + '\n';

    fs.appendFile(log, text, function (err) {
        if (err) throw err;
        console.log('Added to Log!');
    });
}

var ctr = 0
wss.on("connection", function(ws) {
  var id = setInterval(function() {
    var incident = {trafficID:"AKB48", start:"2021-04-25T10:01:05", stop:"2021-04-25T10:02:35", gps:"15,133,12,110"};
    var data = {data:[incident, incident]}
    console.log(data)
    ws.send(JSON.stringify(data), function() {  });

    // addToLog(JSON.stringify(data));

  }, 1000)

  console.log("websocket connection open")

  ws.on("close", function() {
    console.log("websocket connection close")
    clearInterval(id)
  })
})

