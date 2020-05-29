import { h } from 'preact'
import { useEffect, useState } from 'preact/hooks'
import { Link } from 'preact-router/match'

import Thumbnail from './Thumbnail'
import { query } from './graphql'
import './AlbumPage.scss'

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
            attributes {
              width
              height
            }
            iptc {
              caption
              keywords
            }
            xmp {
              rating
            }
            thumbs {
              small {
                src
                size
              }
              medium {
                src
                size
              }
              large {
                src
              }
            }
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

function AlbumPage({ url, ...props }) {
  // Can't use props.matches because preact-router can't match slashes
  const path = url.substr(7)
  const [contents, setAlbum] = useState({});
  useEffect(async () => {
    const { data: { album }, errors } = await query(ALBUM_QUERY, { path })
    setAlbum(album.contents)
  }, [url])

  // console.log('path', path, contents)
  return (<div className="AlbumPage">
    <h2>Album {path}</h2>
    <div className="AlbumPage--flex-container">
      {contents?.edges?.map(({ node }) => (<div className="AlbumPage--tile">
        {node.__typename === 'Album' &&
          <div>Album: <Link href={`/album/${node.path}`}> {node.path}</Link></div>}
        {node.__typename === 'Image' &&
          <div><Thumbnail image={node} /></div>}
      </div>))}
    </div>
  </div>)
}

export default AlbumPage
