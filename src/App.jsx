import { h } from 'preact'
import Router from 'preact-router'

import AlbumPage from './AlbumPage'
import './App.css'


export default function App() {
  return (
    <div className={'App'}>
      <header className="App-header">
        <span>Gallery CMS</span> <small>Metadata based image management</small>
      </header>
      <Router>
        <AlbumPage path="album/:dir" default />
      </Router>
    </div >
  )
}
