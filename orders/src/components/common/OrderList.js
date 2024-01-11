import React from 'react';
import './OrderList.css'; 

function getStatusClassName(status) {
  switch (status) {
    case 'Pending':
      return 'status-pending';
    case 'Out for delivery':
      return 'status-in-transit';
    case 'Delivered':
      return 'status-delivered';
    default:
      return 'status-unknown';
  }
}

function OrderList({ orders, onOrderClick, selectedOrderId }) {
  return (
    <div className="order-list">
      {orders.map(order => (
        <div 
        key={order.order_id} 
        className={`order-item ${order.order_id === selectedOrderId ? 'selected' : ''}`}
        onClick={() => onOrderClick(order)}
        >
          <div><strong>Restaurant:</strong> {order.restaurant_name}</div> {/* Assuming restaurant_name is part of the order object */}
          <div><strong>Total Amount:</strong> ${order.total_amount}</div>
          <div><strong>Order Date:</strong> {order.order_date}</div>
          <div className={`order-status ${getStatusClassName(order.status)}`}>
            <strong>Status:</strong> {order.status}
          </div>
        </div>
      ))}
    </div>
  );
}

export default OrderList;
