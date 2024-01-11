import React, { useState, useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';
import './App.css';
import OrdersComponent from './OrdersComponent';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    const checkAuthentication = () => {
      try {
        const storedIdToken = localStorage.getItem('idToken');
        const storedAccessToken = localStorage.getItem('accessToken');
  
        if (storedIdToken && storedAccessToken) {
          const decodedToken = jwtDecode(storedIdToken);
          setIsAuthenticated(true);
          setUserInfo(decodedToken);
        } else {
          const hash = window.location.hash.substring(1);
          const result = hash.split('&').reduce((res, item) => {
            const parts = item.split('=');
            res[parts[0]] = parts[1];
            return res;
          }, {});
  
          if (result.id_token && result.access_token) {
            localStorage.setItem('idToken', result.id_token);
            localStorage.setItem('accessToken', result.access_token);
            const decodedToken = jwtDecode(result.id_token);
            setIsAuthenticated(true);
            setUserInfo(decodedToken);
          } else {
            redirectToLogin();
          }
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
      }
    };

    checkAuthentication();
  }, []);

  const redirectToLogin = () => {
    window.location.href = 'https://ridertexas.auth.us-east-1.amazoncognito.com/login?client_id=5djc0231nias0s1n72gsgooond&response_type=token&scope=email+openid+phone&redirect_uri=https%3A%2F%2Fkocavs.github.io%2Feat-nyc-delivery%2F';
  };

  const handleLogout = () => {
    // Clear tokens from localStorage and update state
    localStorage.removeItem('idToken');
    localStorage.removeItem('accessToken');
    setIsAuthenticated(false);
    setUserInfo(null);
  };

   return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to Your Delivery App</h1>
      </header>
      {isAuthenticated ? (
        <div className="user-info">
          <p className="user-email">Logged in as: {userInfo?.email}</p>
          <button className="button" onClick={handleLogout}>Logout</button>
          <main>
            <OrdersComponent userInfo={userInfo} />
          </main>
        </div>
      ) : (
        <div className="user-info">
          <p className="user-email">You are not logged in</p>
          <button className="button" onClick={redirectToLogin}>Login</button>
        </div>
      )}
    </div>
  );
}

export default App;
