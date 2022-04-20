const dir = '/var/sftp/myfolder/data/';
const MongoClient = require('mongodb').MongoClient;
const MongoURL = 'mongodb://127.0.0.1:27017';
const database = 'incidentdb'

async function addToDatabase(collection, data){
    MongoClient.connect(MongoURL, {
        useNewUrlParser: true,
        useUnifiedTopology: true
    }, (err, client) => {
        if (err) {
            return console.log(err);
        }
  
        // Specify database you want to access
        const db = client.db(database);
    
        console.log(`MongoDB Connected: ${MongoURL}`);
    
        db.collection(collection).insertOne(data, function(err, res) {
            if (err) throw err;
            console.log("1 document inserted");
        });
    });                     
}
  
function addToLog(data, log) {
    process.env.TZ = "Asia/Manila";
    var date = new Date()
    var time = new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().replace(/T|Z/g, ' '); 
    var details = {trafficID: data.trafficID, datetime: time, client: data.client, info: data}
    
    addToDatabase(log, details)
}

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
module.exports = { dir, MongoURL, database, addToDatabase, addToLog, fileExists };
