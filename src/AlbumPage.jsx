import { h } from 'preact'
import { useEffect, useState } from 'preact/hooks'
import { Link } from 'preact-router/match';

import { query } from './graphql'

const ALBUM_QUERY = `
query GetAlbum($path: String!) {
  album(path: $path) {
    path
    contents {
      pageInfo {
        startCursor
        endCursor
      }
      edges {
        node {
          ... on Image {
            path
            __typename
          }
          ... on Album {
            path
            __typename
          }
        }
      }
    }
  }
}
`

function AlbumPage({ url, ...rest }) {
  console.dir(rest)
  // const path = rest.default ? '.' : 'hmm'
  // Can't use props.matches because preact-router can't match slashes
  const path = url.substr(7)
  const [contents, setAlbum] = useState({});
  useEffect(async () => {
    console.log('fetch start')
    const { data: { album }, errors } = await query(ALBUM_QUERY, { path })
    console.log('fetch done', album)
    setAlbum(album.contents)
  }, [url])

  console.log('path', path, contents)
  return (<div className="Album">
    <h2>Album {path}</h2>
    {contents?.edges?.map(({ node }) => (<div>
      {node.__typename === 'Album' &&
        <div>Album: <Link href={`/album/${node.path}`}> {node.path}</Link></div>}
      {node.__typename === 'Image' &&
        <div>Image: <Link href={`/album/${node.path}`}> {node.path}</Link></div>}
    </div>))}
  </div>)
}

export default AlbumPage
