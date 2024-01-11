import React from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';


function Sidebar({  isAuthenticated, setIsAuthenticated, redirectToLogin, userInfo, setUserInfo }) {
  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('idToken');
    localStorage.removeItem('accessToken');
    setUserInfo(null);
    redirectToLogin()
  };


  return (
    <div className="sidebar">
      <div className="logo">EATexas</div>
      <div className="navigation">
        <NavLink to="/Cloud_Project/homepage" end activeClassName="active" className="nav-button" >ChatBot</NavLink>
        <NavLink to="/Cloud_Project/orders" activeClassName="active" className="nav-button" >Orders</NavLink>
        <NavLink to="/Cloud_Project/reservations" activeClassName="active" className="nav-button" >Reservations</NavLink>
      </div>

      <div className="user-info">
        {isAuthenticated ? (
          <>
            <div className="user-profile">{userInfo.email}</div>
            <button onClick={handleLogout} className="logout-button">Log Out</button>
          </>
        ) : (
          <button onClick={redirectToLogin} className="login-button">Login</button>
        )}
      </div>
    </div>
  );
}

export default Sidebar;
