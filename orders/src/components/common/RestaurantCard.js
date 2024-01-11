import React from 'react';
import './RestaurantCard.css';

function RestaurantCard({ restaurant, onSelect, isSelected }) {
  // You can format the rating to your preference, e.g., showing stars or just the number
  const renderRating = (rating) => {
    return rating ? `${rating} / 5.0` : 'Not Rated';
  };

  return (
    <div 
      className={`restaurant-card ${isSelected ? 'selected' : ''}`} 
      onClick={() => onSelect(restaurant)}
    >
      <h3 className="restaurant-name">{restaurant.name}</h3>
      <div className="restaurant-info">
        <span className="restaurant-price-range">{restaurant.price_range || 'N/A'}</span>
        <span className="restaurant-rating">{renderRating(restaurant.rating)}</span>
      </div>
      <p className="restaurant-category">{restaurant.category}</p>
    </div>
  );
}

export default RestaurantCard;
