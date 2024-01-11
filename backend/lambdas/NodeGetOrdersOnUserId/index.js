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
        const emailId = event.emailId;

        // Ensure that the input is sanitized and safe to use in the query
        // Construct the query to fetch details of the specified order_id
        const orderQuery = 'SELECT * FROM orders WHERE customer_email = $1';
        const orderResult = await client.query(orderQuery, [emailId]);

        // Construct the query to fetch order_items for each order
        const orderItemsQuery = 'SELECT * FROM order_items WHERE order_id = $1';

        // Loop through each order and fetch associated order_items
        for (let i = 0; i < orderResult.rows.length; i++) {
            const orderId = orderResult.rows[i].order_id;
            const orderItemsResult = await client.query(orderItemsQuery, [orderId]);

            // Add the fetched order_items to the respective order in the result
            orderResult.rows[i].order_items = orderItemsResult.rows;
        }

        // Return the details of the orders with associated order_items as a response
        return {
            statusCode: 200,
            body: JSON.stringify(orderResult.rows),
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
