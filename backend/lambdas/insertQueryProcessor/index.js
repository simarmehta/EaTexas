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
// Execute the INSERT query
async function executeInsertQuery(query) {
    const client = await connectToDb();

    try {
        const result = await client.query(query);
        console.log(result.rows[0])
        return result.rows[0]; // Assuming you want the first inserted row ID
    } catch (e) {
        console.error("Error executing query:", e);
        throw e;
    } finally {
        await client.end();
    }
}

exports.handler = async (event) => {
    console.log(event);
    try {
        // Extract the insert query from the SQS event
        const insertQuery = event.query;

        // Run the received insert query
        const insertedRow = await executeInsertQuery(insertQuery);

        return {
            statusCode: 200,
            body: JSON.stringify({ insertedId: insertedRow.order_id })
        };
    } catch (e) {
        console.error("Error processing event:", e);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Failed to execute insert query' })
        };
    }
};

