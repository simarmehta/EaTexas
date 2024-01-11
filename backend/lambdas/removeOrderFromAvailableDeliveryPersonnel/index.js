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

    // Extract the order_id and delivery_person_id from the Lambda event
    const { order_id, delivery_person_id } = event;

    // Begin a transaction
    await client.query('BEGIN');

    // Delete row from AvailableDeliveryPersonnel
    const deleteQuery = 'DELETE FROM AvailableDeliveryPersonnel WHERE deliverypersonnelid = $1';
    await client.query(deleteQuery, [delivery_person_id]);

    // Fetch rows containing the order_id in order_ids
    const fetchQuery = 'SELECT * FROM AvailableDeliveryPersonnel WHERE $1 = ANY (string_to_array(order_ids, $2))';
    const fetchResult = await client.query(fetchQuery, [order_id, ',']);

    // Update rows by removing order_id from order_ids
    const updatePromises = fetchResult.rows.map(async (row) => {
      const updatedOrderIds = row.order_ids.split(',').filter(id => id !== order_id).join(',');
      const updateQuery = 'UPDATE AvailableDeliveryPersonnel SET order_ids = $1 WHERE deliverypersonnelid = $2';
      await client.query(updateQuery, [updatedOrderIds, row.deliverypersonnelid]);
    });
    await Promise.all(updatePromises);

    // Commit the transaction
    await client.query('COMMIT');

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Rows updated successfully' }),
    };
  } catch (err) {
    // Rollback the transaction if any error occurs
    await client.query('ROLLBACK');
    console.error('Error:', err);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Error executing operation: ' + err.message }),
    };
  } finally {
    if (client) {
      await client.end();
    }
  }
};
