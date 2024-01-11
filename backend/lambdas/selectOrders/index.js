const { Client } = require('pg');

async function connectToDb() {
    // Establishes a connection to the PostgreSQL database
    const client = new Client({
        host: "psqldb.c05yoguzmb1y.us-east-1.rds.amazonaws.com",
        database: "eats",
        user: "master",
        password: "master123",
        port: 5432,
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

exports.handler = async (event) => {
    let client;
    try {
        client = await connectToDb();
        
        // Extract the order_id from the Lambda event
        const order_id = event.order_id;

        // Ensure that the input is sanitized and safe to use in the query
        // Construct the query to fetch details of the specified order_id
        const query = `SELECT * FROM Orders WHERE order_id = ${order_id}`;

        // Execute the query and fetch the details of the specified order_id
        const result = await client.query(query);

        // Return the details of the order_id as a response
        return {
            statusCode: 200,
            body: JSON.stringify(result.rows),
        };

    } catch (err) {
        console.error('Error:', err);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Error executing query: ' + err.message }),
        };

    } finally {
        if (client) {
            await client.end();
        }
    }
};
