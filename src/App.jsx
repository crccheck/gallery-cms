import { h } from 'preact';
import Router from 'preact-router';

import AlbumPage from './AlbumPage'
import './App.css';

function App() {
  return (
    <div className={'App'}>
      <header className="App-header">
        Gallery CMS
      </header>
      <Router>
        <AlbumPage path="album/:dir" default />
      </Router>
    </div >
  );
}

export default App;
