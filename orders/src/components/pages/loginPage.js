
import React from 'react';

function LoginPage({ redirectToLogin }) {
  return (
    <div>
      <h1>Login Page</h1>
      <button onClick={redirectToLogin}>Login with Cognito</button>
    </div>
  );
}

export default LoginPage;
