import React, { useState, useEffect } from 'react';
import apigClient from './apigClient'
import './OrdersComponent.css'

function OrdersComponent({ userInfo }) {
  const [orders, setOrders] = useState([]);
  const [intervalIds, setIntervalIds] = useState({});
  const [isAvailableForDelivery, setIsAvailableForDelivery] = useState(false);
  const deliveryPersonnelId = "dhiren7motwani@gmail.com"; // Example email
  const pincode = '75057'; // Hardcoded pincode


  useEffect(() => {
    // Clean up any intervals and remove them from the state when the component unmounts
    return () => {
      Object.values(intervalIds).forEach((intervalId) => clearInterval(intervalId));
    };

  }, []);

  const makeAvailableForDelivery = () => {
    // Prepare the request body
    const body = {
        "deliveryPersonnelId": deliveryPersonnelId,
        "pincode": pincode
    };

    // Call availableForDelivery API with the body
    apigClient.availableforDeliveryPost({}, body, {})
      .then(response => {
        console.log('Available for delivery:', response.data);
        setIsAvailableForDelivery(true);
      })
      .catch(error => console.error('Error making available for delivery:', error));
  };

  const showAvailableOrders = () => {
    const params = { "user_id": deliveryPersonnelId };
    apigClient.ordersGet(params, {})
      .then(response => {
        console.log(response.data);
        displayOrders(response.data);
      })
      .catch(error => console.error('Error fetching orders:', error));
  };
  
  const displayOrders = (ordersData) => {
    try {
      // First parse the outer array
      const outerArray = JSON.parse(ordersData.body);
  
      // Now parse each order string in the outer array
      let parsedOrders = outerArray.map(orderString => JSON.parse(orderString.body));
      parsedOrders = parsedOrders.flat();
      setOrders(parsedOrders);
    } catch (error) {
      console.error('Error parsing orders:', error);
      setOrders([]); // Reset orders on error
    }
  };

  function startDelivery(orderId) {
    // Call startOrderDeliveryPut API first
    const startOrderBody = {
      "order_id": String(orderId),
      "delivery_person_id": deliveryPersonnelId
    }; 

    apigClient.startOrderDeliveryPut({}, startOrderBody, {})
      .then(response => {
        console.log('Order delivery started:', response.data);
        
        // Start sending location updates
        const intervalId = setInterval(function () {
          navigator.geolocation.getCurrentPosition(function (position) {
            const location = {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
            };
  
            sendLocation(orderId, location);
          });
        }, 15000);
  
        // Store the intervalId in state with orderId as the key
        setIntervalIds(prevIntervalIds => ({
          ...prevIntervalIds,
          [orderId]: intervalId,
        }));
      })
      .catch(error => {
        console.error('Error starting order delivery:', error);
      });
  }
  
  function sendLocation(orderId, location) {
    const params = {};
    const body = { "order_id": String(orderId), "location": location };

    // Call API Gateway endpoint to send the location
    apigClient.locationPut(params, body, {})
      .then(function (result) {
        console.log('Location sent successfully:', result.data);
      })
      .catch(function (err) {
        console.error('Error sending location:', err);
      });
  }

  const completeDelivery = (orderId) => {
    clearInterval(intervalIds[orderId]);

    const params = {};
    const body = { "order_id": String(orderId) };

    apigClient.completeDeliveryPut(params, body)
      .then(response => {
        console.log('Delivery completed:', response.data);
        // Optionally, update orders state to reflect delivery completion
      })
      .catch(error => console.error('Error completing delivery:', error));
  };



 return (
  <div className="delivery-container">
    {!isAvailableForDelivery && (
      <button className="delivery-button" onClick={makeAvailableForDelivery}>
        Make Available for Delivery
      </button>
    )}
    {isAvailableForDelivery && (
      <>
        <button className="delivery-button" onClick={showAvailableOrders}>
          Show Available Orders
        </button>
        {orders.length > 0 ? (
          <ul className="order-list">
            {orders.map((order) => (
              <li key={order.order_id} className="order-item">
                <p className="order-detail">Order ID: {order.order_id}</p>
                <button className="delivery-button" onClick={() => startDelivery(order.order_id)}>
                  Start Delivery
                </button>
                <button className="delivery-button" onClick={() => completeDelivery(order.order_id)}>
                  Complete Delivery
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p>No orders available.</p>
        )}
      </>
    )}
  </div>
  );
}

export default OrdersComponent;
