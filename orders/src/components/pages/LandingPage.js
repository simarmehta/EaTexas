// LandingPage.js
import React from 'react';
import './LandingPage.css';

function LandingPage({redirectToLogin}) {


  const backgroundStyle = {
    backgroundImage: `url(${process.env.PUBLIC_URL + '/assets/img/landingPage.png'})`,
    backgroundSize: 'cover',
    width: '100vw',
    backgroundPosition: 'center',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    textAlign: 'center'
  };

  return (
    <div style={backgroundStyle}>
      <h1>Welcome to Our Food Delivery Service</h1>
      <button onClick={redirectToLogin}>Get Started</button>
    </div>
  );
}

export default LandingPage;
