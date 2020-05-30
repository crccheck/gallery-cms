import { h } from 'preact'
import { useEffect, useState } from 'preact/hooks'
import { Link } from 'preact-router/match'

import AppContext from './AppContext'
import RatingMenu from './RatingMenu'
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
            }
            src
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

  // WISHLIST persist ratings to localStorage
  const [ratingsVisible, setRatingsVisible] = useState(new Set('012345'))
  const [contents, setAlbum] = useState({})
  useEffect(async () => {
    const { data: { album }, errors } = await query(ALBUM_QUERY, { path })
    setAlbum(album.contents)
  }, [url])

  function toggleRating(rating) {
    if (ratingsVisible.has(rating)) {
      ratingsVisible.delete(rating)
    } else {
      ratingsVisible.add(rating)
    }
    setRatingsVisible(new Set(ratingsVisible))
  }

  const visibleRatingsClass = [...ratingsVisible].map((x) => `show-rating-${x}`).join(' ')
  return (
    <AppContext.Provider value={{ ratingsVisible, toggleRating }}>
      <div className="AlbumPage Page">
        <div className="Page--LeftRail">
          <RatingMenu />
        </div>
        <div className="Page--Main">
          <h2>Album {path}</h2>
          <div className={`AlbumPage--flex-container ${visibleRatingsClass}`}>
            {contents?.edges?.map(({ node }) => (
              <div className={`AlbumPage--tile rating-${node?.xmp?.rating}`}>
                {node.__typename === 'Album' &&
                  <div>Album: <Link href={`/album/${node.path}`}> {node.path}</Link></div>}
                {node.__typename === 'Image' &&
                  <Thumbnail image={node} />}
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppContext.Provider>
  )
}

export default AlbumPage
