const { Client } = require('pg');

exports.handler = async (event) => {
    const { order_id, deliverypersonnelid } = event;

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

        const checkQuery = 'SELECT * FROM AvailableDeliveryPersonnel WHERE deliverypersonnelid = $1';
        const checkResult = await client.query(checkQuery, [deliverypersonnelid]);

        let existingOrderIds = '';
        if (checkResult.rows.length > 0) {
            existingOrderIds = checkResult.rows[0].order_ids || '';
        }

        existingOrderIds = existingOrderIds ? `${existingOrderIds},${order_id}` : order_id;

        if (checkResult.rows.length > 0) {
            const updateQuery = 'UPDATE AvailableDeliveryPersonnel SET order_ids = $1 WHERE deliverypersonnelid = $2';
            await client.query(updateQuery, [existingOrderIds, deliverypersonnelid]);
        } else {
            const insertQuery = 'INSERT INTO AvailableDeliveryPersonnel (deliverypersonnelid, order_ids) VALUES ($1, $2)';
            await client.query(insertQuery, [deliverypersonnelid, existingOrderIds]);
        }

        return { statusCode: 200, body: JSON.stringify({ message: 'Operation successful' }) };
    } catch (err) {
        console.error('Error:', err);
        return { statusCode: 500, body: JSON.stringify({ error: 'Error processing request: ' + err.message }) };
    } finally {
        await client.end();
    }
};
