const http_port = 8080

const fs = require('fs'); 
var express = require("express")
var app = express()
// Static Files are in current directory
app.use(express.static(__dirname + "/"))
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.set('view engine', 'ejs');

const MongoClient = require('mongodb').MongoClient;

const { dir, MongoURL, database, addToDatabase, removeFromDatabase, addToLog, fileExists } = require("./lib");

app.listen(http_port, () => console.log('HTTP Server Listening on %d', http_port))
app.get('/', (req, res) => {
  	res.render('index');              
});


app.get('/create', (req, res) => {
  	res.render('create');              
});

app.post('/create', (req, res) => {
	data = req.body
	trafficID = data.trafficID
	dates = data.datetimes.split(" - ")
	start = dates[0].replace(" ", "T")
	end = dates[1].replace(" ", "T")
	gps = data.gps1x + "," + data.gps1y + "," + data.gps2x + "," + data.gps2y
	var target = {
		trafficID:trafficID, 
		start:start, 
		stop:end, 
		gps:gps
	};
	console.log(data)
	console.log(target)
	addToDatabase('requests', target).catch(console.error);
	res.redirect("/view/request");
})

app.get('/view/request', (req, res) => {
	MongoClient.connect(MongoURL, (err, client) => {
		if (err) return console.log(err);

		const db = client.db(database);
		console.log(`MongoDB Connected: ${MongoURL}`);
		const col = db.collection('requests');
		col.find().toArray((err, results) => {
			console.log(results);
			res.render('request', {data:results});
			client.close();

		});
	});                    
});

app.get('/view/response', (req, res) => {
	fs.readdir(dir, function (err, files) {
		if (err) return console.log('Unable to scan directory: ' + err);
		res.render('response', {data:files});
	});                  
});


app.get('/logs/request', (req, res) => {
	MongoClient.connect(MongoURL, (err, client) => {
		if (err) return console.log(err);

		const db = client.db(database);
		console.log(`MongoDB Connected: ${MongoURL}`);
		const col = db.collection('logs_ws');
		col.find().toArray((err, results) => {
			console.log(results);
			client.close();
			res.render('log', {data:results, page:"Request"});
		});
	});                    
});

app.get('/logs/response', (req, res) => {
	MongoClient.connect(MongoURL, (err, client) => {
		if (err) return console.log(err);

		const db = client.db(database);
		console.log(`MongoDB Connected: ${MongoURL}`);
		const col = db.collection('logs_sftp');
		col.find().toArray((err, results) => {
			console.log(results);
			client.close();
			res.render('log', {data:results, page:"Response"});
		});
	});                    
});

app.get('/videos/:id', function(req, res) {
	const id =req.params.id;

	// Ensure there is a range given for the video
	const range = req.headers.range ? req.headers.range : 'bytes=0-';
	if (!range) res.status(400).send("Requires Range header");

	// get video stats (about 61MB)
	const videoPath = dir + id+".mp4";
	const videoSize = fs.statSync(videoPath).size;

	// Parse Range
	// Example: "bytes=32324-"
	const CHUNK_SIZE = 10 ** 6; // 1MB
	const start = Number(range.replace(/\D/g, ""));
	const end = Math.min(start + CHUNK_SIZE, videoSize - 1);

	// Create headers
	const contentLength = end - start + 1;
	const headers = {
		"Content-Range": `bytes ${start}-${end}/${videoSize}`,
		"Accept-Ranges": "bytes",
		"Content-Length": contentLength,
		"Content-Type": "video/mp4",
	};

	// HTTP Status 206 for Partial Content
	res.writeHead(206, headers);

	// create video read stream for this particular chunk
	const videoStream = fs.createReadStream(videoPath, { start, end });

	// Stream the video chunk to the client
	videoStream.pipe(res);
});

app.delete('/remove/:id',(req,res)=>{
	const collection =req.params.id;
	const id = req.body.id;
	console.log("From", collection)
	if (collection == 'responses'){
		console.log("Deleting video", id);
		fs.unlink(dir+id, function (err) {
			if (err) res.json({msg:'error'});
			// if no error, file has been deleted successfully
			res.json({msg:'success'})
		});
	}
	else{
		console.log("Deleting ", id)
		removeFromDatabase(collection, id)
			.then((result) => {
				if (result.deletedCount == 1) return res.json({msg:'success'})
				else res.json({msg:'error'})
			})
			.catch((result) => {
				res.json({msg:'error'})
			  }
			)
	}
});  

module.exports = app