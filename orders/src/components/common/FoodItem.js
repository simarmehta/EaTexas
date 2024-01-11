// components/FoodItem.js
import React from 'react';
import './FoodItem.css';

function FoodItem({ data }) {
  return (
    <div className="food-item">
      <img src={data.imageUrl} alt={data.title} className="food-image" />
      <div className="food-info">
        <h3 className="food-title">{data.title}</h3>
        <p className="food-description">{data.description}</p>
        {/* You can add more details like ratings, price etc. here */}
      </div>
      {/* Add action buttons if needed */}
    </div>
  );
}

export default FoodItem;
