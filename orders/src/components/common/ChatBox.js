import React, { useState, useEffect, useCallback } from 'react';
import './ChatBox.css';
import apigClient from '../../api/apigClient';

function convertToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
  });
}


function ChatBox({ webSocket, messages, setMessages }) {

  const [newMessage, setNewMessage] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewImage, setPreviewImage] = useState(null);
  
  const scrollToBottom = useCallback(() => {
    const chatMessages = document.querySelector('.chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSendMessage = async () => {
    if (newMessage.trim() === '' && !selectedFile) return;
    
    let base64Image;
    if (selectedFile) {
      try {
        base64Image = await convertToBase64(selectedFile);
      } catch (error) {
        console.error('Error converting image:', error);
        return;
      }
    }

    const messageBody = { 
      sender: 'user', 
      text: newMessage, 
      image: base64Image || null
    };

    const messageToSend = {
      action: "sendMessage",
      body: messageBody
    };
    
    
    setMessages(prevMessages => [...prevMessages, messageBody]);
    setNewMessage('');
    setSelectedFile(null);
    setPreviewImage(null);

    // Send message through WebSocket
    if (webSocket && webSocket.readyState === WebSocket.OPEN) {
        webSocket.send(JSON.stringify(messageToSend));
    } else {
        console.error('WebSocket is not connected.');
    }
};
  

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      handleSendMessage();
      event.preventDefault();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && ['image/jpeg', 'image/png'].includes(file.type)) {
      setSelectedFile(file);
      const imageUrl = URL.createObjectURL(file);
      setPreviewImage(imageUrl); // New state for previewing the image
    }
  };

  return (
    <div className="chatbox">
      <div className="chat-header">
        <h2>Chat Chat</h2>
      </div>
      <div className="chat-messages">
        {messages.map((message, index) => (
          <Message key={index} message={message} />
        ))}
      </div>
      <MessageInput
        newMessage={newMessage}
        setNewMessage={setNewMessage}
        handleKeyDown={handleKeyDown}
        handleSendMessage={handleSendMessage}
        handleFileChange={handleFileChange}
      />
    </div>
  );
}

const Message = ({ message }) => (
  <div className={`message ${message.sender}`}>
    {message.text && <div>{message.text}</div>}
    {message.image && <img src={message.image} alt="Uploaded" />}
  </div>
);

const MessageInput = ({ newMessage, setNewMessage, handleKeyDown, handleSendMessage, handleFileChange }) => (
  <div className="message-input">
    <div className="file-upload-container">
      <input
        type="file"
        accept="image/jpeg, image/png, image/jpg"
        onChange={handleFileChange}
      />
    </div>
    <div className="text-input-container">
      <input
        type="text"
        value={newMessage}
        onChange={(e) => setNewMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Send a message..."
      />
    </div>
    <button onClick={handleSendMessage}>Send</button>
  </div>
);

export default ChatBox;
