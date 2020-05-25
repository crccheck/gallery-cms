import { h } from 'preact';

import Album from './Album'
import logo from './logo.png';
import './App.css';

function App() {
  return (
    <div className={'App'}>
      <header className="App-header">
        Learn Preact
      </header>
      <Album path="." />
    </div >
  );
}

export default App;
