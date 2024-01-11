import React, {useState, useEffect} from 'react';
import './OrderPage.css'; 
import OrderList from '../common/OrderList';
import OrderDetails from '../common/OrderDetails';
import apigClient from '../../api/apigClient';

function OrderPage({ userInfo }) {
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);

  const handleOrderClick = (order) => {
    setSelectedOrder(order);
  };

  useEffect(() => {
    const params = {
        user_id: userInfo.email      
    };

    apigClient.ordersGet(params,{}, {})
      .then(response => {
        console.log(response.data.body);
        setOrders(response.data.body); // Update with your actual data structure
        setIsLoading(false);
      })
      .catch(error => {
        console.error("Error fetching orders:", error);
        setIsLoading(false);
      });
  }, []); // Empty array ensures this runs once on component mount


  if (isLoading) {
    return <div className="order-page">Loading orders...</div>;
  }

  return (
    <div className="order-page">
      <div className="orders">
        <OrderList 
        orders={orders} 
        onOrderClick={handleOrderClick} 
        selectedOrderId={selectedOrder ? selectedOrder.order_id : null}/>
      </div>
      <div className="order-details">
        {selectedOrder && <OrderDetails order={selectedOrder} />}
      </div>
    </div>
  );
}

export default OrderPage;