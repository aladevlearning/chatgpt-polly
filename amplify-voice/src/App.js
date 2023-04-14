
import {
  AmazonAIPredictionsProvider, Predictions
} from '@aws-amplify/predictions';
import { withAuthenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { faCircleStop, faMicrophone, faUser, faXmarkCircle } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Amplify, API } from 'aws-amplify';
import React, { useState } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { VerticalTimeline, VerticalTimelineElement } from 'react-vertical-timeline-component';
import 'react-vertical-timeline-component/style.min.css';
import alaLogo from "./ala.jpg";
import './App.css';
import awsconfig from './aws-exports';
import chatGptLogo from "./chatgpt_logo.webp";

import { FileUploader } from '@aws-amplify/ui-react';

Amplify.configure(awsconfig);
Amplify.addPluggable(new AmazonAIPredictionsProvider());


function App({ signOut, user }) {

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  const [timelines, setTimelines] = useState([]);
  const [lineColor, setLineColor] = useState("#21223C");
  const [isListening, setIsListening] = useState(false);


  if (!browserSupportsSpeechRecognition) {
    return <span>Browser doesn't support speech recognition.</span>;
  }


  const startListening = () => {
    setIsListening(true);
    SpeechRecognition.startListening({ continuous: true });
  }

  const reset = () => {
    setIsListening(false);
    stopListening();
  }
  const stopListening = async () => {

    await SpeechRecognition.stopListening();

    setIsListening(false);

    if (!transcript) {
      resetTranscript();
      return;
    }

    setTimelines((prevTimelines) => [
      ...prevTimelines,
      <VerticalTimelineElement
        className="vertical-timeline-element--work speaker"
        iconStyle={{ background: 'rgb(33, 150, 243)', color: '#fff' }}
        icon={user.username === "ala" ? <img src={alaLogo} alt="User logo" /> : <FontAwesomeIcon icon={faUser}></FontAwesomeIcon>}
      >
        <div>{transcript.slice()}</div>
      </VerticalTimelineElement>
    ]);

    setLineColor("white");

    const completion = await API.post('apiAskChatGpt', '/askWithDocument', {
      body: {
        input: {
          question: transcript
        }
      },
    });

    resetTranscript();

    setTimelines((prevTimelines) => [
      ...prevTimelines,
      <VerticalTimelineElement
        className="vertical-timeline-element--work bot"
        iconStyle={{ background: 'rgb(33, 150, 243)', color: '#fff' }}
        icon={<picture>
          <img src={chatGptLogo} alt="chatgpr logo" />
        </picture>}
      >
        <div>{completion.Answer}</div>
      </VerticalTimelineElement>
    ]);

    const result = await Predictions.convert(
      {
        textToSpeech: {
          source: {
            //text: completion.data.choices[0].text,
            text: completion.Answer,
          },
          voiceId: "Joanna" // default configured on aws-exports.js
          // list of different options are here https://docs.aws.amazon.com/polly/latest/dg/voicelist.html
        }
      }
    );

    let AudioContext = window.AudioContext || window.webkitAudioContext;
    console.log({ AudioContext });
    const audioCtx = new AudioContext();
    const source = audioCtx.createBufferSource();


    audioCtx.decodeAudioData(result.audioStream, (buffer) => {

      source.buffer = buffer;
      source.connect(audioCtx.destination);
      source.start(0);
    });

    document.addEventListener('touchend', ()=> AudioContext.resume());
  }


  return (
    <div className="App">
      <header>
        <nav className="bg-white border-gray-200 px-4 lg:px-6 py-2.5 dark:bg-gray-800">
          <div className="flex flex-wrap justify-between items-center mx-auto max-w-screen-xl">     
              <span className="self-center text-xl font-semibold whitespace-nowrap dark:text-white">Welcome {user.username}</span>
            <div>
              {!isListening ? <FontAwesomeIcon icon={faMicrophone} className={`mic-off ${listening ? " listening" : ""}`} onClick={startListening} /> : null}
              {isListening ? <FontAwesomeIcon icon={faCircleStop} className={`stop ${listening ? " listening" : ""}`} onClick={stopListening} /> : null}
              {isListening ? <FontAwesomeIcon icon={faXmarkCircle} className={`cancel ${listening ? " listening" : ""}`} onClick={reset} /> : null}
            </div>
            <div className="flex items-center lg:order-2">
              <a className="text-gray-800 dark:text-white hover:bg-gray-50 focus:ring-4 focus:ring-gray-300 font-medium rounded-lg text-sm px-4 lg:px-5 py-2 lg:py-2.5 mr-2 dark:hover:bg-gray-700 focus:outline-none dark:focus:ring-gray-800" onClick={signOut}>Log out</a>
            </div>
          </div>
        </nav>
      </header>
      <div style={styles.container}>
       <FileUploader
            acceptedFileTypes={['text/*']}
            accessLevel="private"
          />
      </div>
      <VerticalTimeline
        lineColor = {lineColor}
      >
        {timelines.map((timeline, i) => {
          return (timeline)
        })}
      </VerticalTimeline>
    </div>
  );
}

const styles = {
  container: { width: 400, margin: '0 auto', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: 20 },
  todo: { marginBottom: 15 },
  input: { border: 'none', backgroundColor: '#ddd', marginBottom: 10, padding: 8, fontSize: 18 },
  todoName: { fontSize: 20, fontWeight: 'bold' },
  todoDescription: { marginBottom: 0 },
  button: { backgroundColor: 'black', color: 'white', outline: 'none', fontSize: 18, padding: '12px 0px' }
}

export default withAuthenticator(App, { hideSignUp: false });
