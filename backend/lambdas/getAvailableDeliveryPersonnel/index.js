const { Client } = require('pg');

exports.handler = async (event) => {
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

// exports.handler = async (event) => {
  const pincodeInput = event.pincode;

  try {
    await client.connect();

    const query = `
      SELECT deliverypersonnelid, pincode
      FROM AvailableDeliveryPersonnel
      WHERE pincode = $1 OR pincode IN (
        SELECT pincode
        FROM AvailableDeliveryPersonnel
        ORDER BY ABS(CAST(pincode AS INTEGER) - CAST($2 AS INTEGER))
        LIMIT 1
      );
    `;

    const res = await client.query(query, [pincodeInput, pincodeInput]);

    if (res.rows.length > 0) {
      console.log(res.rows);
      return {
        statusCode: 200,
        body: JSON.stringify(res.rows),
      };
    } else {
      return {
        statusCode: 404,
        body: JSON.stringify({ message: 'No matching delivery personnel found' }),
      };
    }
  } catch (err) {
    console.error('Error:', err);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Error executing query: ' + err.message }),
    };
  } finally {
    await client.end();
  }
};
