const { Client } = require('pg');

// Establish a connection to RDS
async function connectToDb() {
    // Your connection details
    const client = new Client({
        host: "psqldb.c05yoguzmb1y.us-east-1.rds.amazonaws.com",
        database: "eats",
        user: "master",
        password: "master123",
        port: 5432, // Default PostgreSQL port
        ssl: {
            rejectUnauthorized: false // Not recommended for production; use CA certificate
        }
    });

    try {
        await client.connect();
        return client;
    } catch (e) {
        console.error("Failed to connect to DB:", e);
        throw e;
    }
}

// Update the status in the RDS table
async function updateQuery(query) {
    let client;
    try {
        client = await connectToDb();
        await client.query(query);
    } catch (e) {
        console.error("Error updating", e);
        throw e;
    } finally {
        if (client) {
            await client.end();
        }
    }
}

exports.handler = async (event) => {
    console.log(event);
    try {
        // Extract the query from the SQS event
        const query = event.Records[0].body;
        console.log(query)
        // Run the received query
        await updateQuery(query);
    } catch (e) {
        console.error("Error processing event:", e);
        throw e;
    }
};
