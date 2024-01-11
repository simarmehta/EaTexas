import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import RestaurantCard from './RestaurantCard';
import RestaurantDetail from './RestaurantDetail';
import './FoodRecommendation.css';
import apigClient from '../../api/apigClient';


function FoodRecommendation({ recommendationsInput }) {
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (recommendationsInput && recommendationsInput.length > 0) {
      setRecommendations(recommendationsInput);
      setIsLoading(false);
    }else{
      setIsLoading(true);
    }
  }, [recommendationsInput]);

  const handleSelectRestaurant = (restaurant) => {
    setSelectedRestaurant(restaurant);
  };

  return (
    <div className="food-recommendation">
      <div className="food-recommendation-header">
        <h2>Food Recommendations</h2>
        {isLoading && <p>Loading...</p>}
        {error && <p className="error">{error}</p>}
      </div>
      <div className="restaurant-cards">
        {recommendations.map((restaurant) => (
          <RestaurantCard
            key={restaurant.id}
            restaurant={restaurant}
            onSelect={handleSelectRestaurant}
            isSelected={selectedRestaurant && selectedRestaurant.id === restaurant.id}
          />
        ))}
      </div>
      {selectedRestaurant && <RestaurantDetail restaurant={selectedRestaurant} />}
    </div>
  );
}

FoodRecommendation.propTypes = {
  initialRecommendations: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    full_address: PropTypes.string.isRequired,
    category: PropTypes.string.isRequired,
    price_range: PropTypes.string,
    score: PropTypes.string,
    ratings: PropTypes.string,
    lat: PropTypes.string,
    lng: PropTypes.string,
    position: PropTypes.string
    // Add any other relevant PropTypes based on your data structure
  }))
};

export default FoodRecommendation;
