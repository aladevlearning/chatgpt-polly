import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { Amplify } from 'aws-amplify';
import awsExports from './aws-exports';

window.Buffer = window.Buffer || require("buffer").Buffer;

Amplify.configure(awsExports);


Amplify.configure({
  API: {
      endpoints: [
          {
              name: "apiAskChatGpt",
              endpoint: "https://wko2ca34z0.execute-api.eu-west-1.amazonaws.com/dev"
          }
      ]
  }
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
