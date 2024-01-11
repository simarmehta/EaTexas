import React, {useEffect, useState}from 'react';
import { GoogleMap, Marker, LoadScript } from '@react-google-maps/api';

function DeliveryMap({ deliveryLocation, restaurantLocation, orderStatus, deliveryPositions}) {
    const [userLocation, setUserLocation] = useState(null);
    const mapContainerStyle = {
        height: '400px',
        width: '100%'
    };

    useEffect(() => {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(position => {
            setUserLocation({
              lat: position.coords.latitude,
              lng: position.coords.longitude
            });
          }, err => {
            console.warn(`ERROR(${err.code}): ${err.message}`);
          });
        }
      }, []);

    // const center = orderStatus === 'Out For Delivery' ? deliveryLocation : restaurantLocation;
      const center = restaurantLocation;
    const createIcon = (iconPath) => {
        return {
            url: iconPath
        };
    };
    return (
        <LoadScript googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY}>
            <GoogleMap
                mapContainerStyle={mapContainerStyle}
                center={center}
                zoom={15}
            >
                {deliveryLocation && <Marker
                position={deliveryLocation}
                title="Delivery Person"
                icon={createIcon(process.env.PUBLIC_URL + '/assets/img/delivery.svg')}
                />}

                {restaurantLocation && <Marker
                position={restaurantLocation}
                title="Restaurant"
                icon={createIcon(process.env.PUBLIC_URL + '/assets/img/restaurant.svg')}
                />}

                {userLocation && <Marker
                position={userLocation}
                title="Customer"
                icon={createIcon(process.env.PUBLIC_URL + '/assets/img/customer.svg')}
                />}

                {deliveryPositions && deliveryPositions.map((position, index) => (
                    <Marker
                        key={index}
                        position={{ lat: position.lat, lng: position.lng }}
                        title={`Delivery Position ${index + 1}`}
                    />
                ))}

            </GoogleMap>
        </LoadScript>
    );
}

export default DeliveryMap;
