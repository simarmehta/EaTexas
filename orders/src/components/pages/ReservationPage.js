import React, { useEffect, useState } from 'react';
import apigClient from '../../api/apigClient';
import './ReservationPage.css'; 

function ReservationPage({ userInfo }) {
    const [reservations, setReservation] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    
    useEffect(() => {
      const params = {
          email: userInfo.email      
      };
  
      apigClient.getReservationDetailsGet(params,{}, {})
        .then(response => {
          const responseBody = JSON.parse(response.data.body);
          console.log(responseBody);
      
          // Access the reservations array and update the state
          setReservation(responseBody.reservations);
       // Update with your actual data structure
          setIsLoading(false);
        })
        .catch(error => {
          console.error("Error fetching orders:", error);
          setIsLoading(false);
        });
    }, []);

    return (
        <div className="container">
          <h1 className="header">Reservations for {userInfo.email}</h1>
          {reservations.length > 0 ? (
            reservations.map((reservation, index) => (
              <div key={index} className="reservation-card">
                <div className="reservation-detail">Restaurant ID: {reservation.rest_id}</div>
                <div className="reservation-detail">People: {reservation.people}</div>
                <div className="reservation-detail">Date: {reservation.date}</div>
                <div className="reservation-detail">Time: {reservation.time}</div>
              </div>
            ))
          ) : (
            <p>No reservations found.</p>
          )}
        </div>
      );
}

export default ReservationPage;