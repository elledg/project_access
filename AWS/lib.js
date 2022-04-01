// const dir = '/var/sftp/myfolder/data/';
const dir = '/home/arae/Desktop/Thesis/project_access/RPi/files/output/'
const MongoClient = require('mongodb').MongoClient;
const mongodb = require('mongodb');
const MongoURL = 'mongodb://127.0.0.1:27017';
const database = 'incidentdb'
const fs = require('fs'); 

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
            client.close();
        });
    });                     
}

async function removeFromDatabase(collection, id){
    const client = await MongoClient.connect(MongoURL, { useNewUrlParser: true })
        .catch(err => { console.log(err); });
    if (!client) return;

    try {
        const db = client.db(database);
        var data = {_id: new mongodb.ObjectID(id)}
        let result = await db.collection(collection).deleteOne(data)
        // console.log(result)
        return result
    } 
    catch (err) {
        console.log(err); 
        throw err;
    }
    finally {
        client.close();
    }
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
    fs.stat(dir, function (err, stats) {
        console.log(stats);//here we got all information of file in stats variable
     
        if (err) {
            console.error(err);
            return false
        }
        return true
     });
     
    // try {
    //     const files = fs.readdirSync(dir);

    //     // files object contains all files names
    //     for (let i = 0; i < files.length; i++) {
    //         file = files[i];
    //         var name = file.split(".")[0]
    //         if (name == trafficID){
    //             console.log(trafficID + " found")
    //             return true
    //         }
    //     }
    //     return false
    // } catch (err) {
    //     console.log(err);
    // }
}
module.exports = { dir, MongoURL, database, addToDatabase, removeFromDatabase, addToLog, fileExists };
