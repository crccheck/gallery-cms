import { h } from 'preact'
import { useEffect, useState } from 'preact/hooks'
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

function Album({ path = '.' }) {
  const [contents, setAlbum] = useState({});
  useEffect(async () => {
    console.log('fetch start')
    const { data: { album }, errors } = await query(ALBUM_QUERY, { path })
    console.log('fetch done', album)
    setAlbum(album.contents)
  }, [])

  console.log('path', path, contents)
  return (<div className="Album">
    <h2>Album {path}</h2>
    {contents?.edges?.map(({ node }) => (<div>
      Album: {node.path}
    </div>))}
  </div>)
}

export default Album
