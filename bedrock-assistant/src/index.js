import React, {StrictMode } from "react";
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import {BrowserRouter} from "react-router-dom" 
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
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
