// pages/HomePage.js
import React, { useState, useEffect }  from 'react';
import ChatBox from '../common/ChatBox';
import './HomePage.css'
import FoodRecommendation from '../common/FoodRecommendation';

function HomePage({ userInfo }) {
  const [webSocket, setWebSocket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [foodRecommendations, setFoodRecommendations] = useState([]);

  useEffect(() => {
    // Initialize WebSocket connection
    const ws = new WebSocket('wss://gnzcvg3d4l.execute-api.us-east-1.amazonaws.com/test/');

    ws.onopen = () => {
        console.log('WebSocket Connected');
        setWebSocket(ws);
    };

    ws.onmessage = (event) => {
        // Handle incoming WebSocket messages
        const message = JSON.parse(event.data);
        console.log('Received:', message);
        if (message.sender === "bot") {
          let botMessages = [];
  
          if (Array.isArray(message.text)) {
              // If 'text' is an array, map each text entry to a message object
              botMessages = message.text.map(text => ({
                  sender: "bot",
                  text: text,
                  image: null // Assuming no image in bot responses
              }));
          } else if (typeof message.text === 'string') {
              // If 'text' is a string, create a single message object
              botMessages = [{
                  sender: "bot",
                  text: message.text,
                  image: null
              }];
          }
          // Update the messages state with new bot messages
          setMessages(prevMessages => [...prevMessages, ...botMessages]);
        }else if(message.sender === "foodRecommend"){
          const recommendations = JSON.parse(message.text);
          console.log(recommendations)
          if (Array.isArray(recommendations)) {
            setFoodRecommendations(recommendations);
          }
        }
        

        // TODO: Add logic to handle the message and potentially forward it to ChatBox or FoodRecommendation
    };

    ws.onclose = () => {
        console.log('WebSocket Disconnected');
        setWebSocket(null);
    };

    return () => {
        // Clean up WebSocket connection on component unmount
        ws.close();
    };
  }, []);

  return (
    <div className="home-page">
      <ChatBox className="chat-area" webSocket={webSocket} messages={messages} setMessages={setMessages} />
      <FoodRecommendation recommendationsInput={foodRecommendations} className="food-recommendation" webSocket={webSocket}  />
      {/* Add other components specific to the homepage here */}
    </div>
  );
}

export default HomePage;
