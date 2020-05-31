import { h } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';
import { Link } from 'preact-router/match';

import AppContext from './AppContext';
import AlbumThumb from './AlbumThumb';
import RatingMenu from './RatingMenu';
import Thumbnail from './Thumbnail';
import { query } from './graphql';
import './AlbumPage.scss';

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
`;

function AlbumPage({ url, ...props }) {
  // Can't use props.matches because preact-router can't match slashes
  const path = url.substr(7);

  const [ratingsVisible, setRatingsVisible] = useState(
    new Set(localStorage.getItem('gcms:ratingsVisible') || '012345')
  );
  const [contents, setAlbum] = useState({});
  const ratingMenu = useRef(null);
  useEffect(() => {
    let ticking = false;
    window.addEventListener('scroll', (e) => {
      if (!ticking) {
        setTimeout(() => {
          ratingMenu.current.base.style.top = `${window.scrollY}px`
          ticking = false;
        }, 300);
        ticking = true;
      }
    }, { passive: true });
  }, []);
  useEffect(async () => {
    const {
      data: { album },
      errors,
    } = await query(ALBUM_QUERY, { path });
    setAlbum(album.contents);
  }, [url]);

  function toggleRating(rating) {
    if (ratingsVisible.has(rating)) {
      ratingsVisible.delete(rating);
    } else {
      ratingsVisible.add(rating);
    }
    localStorage.setItem('gcms:ratingsVisible', [...ratingsVisible].join(''));
    setRatingsVisible(new Set(ratingsVisible));
  }

  const visibleRatingsClass = [...ratingsVisible].map((x) => `show-rating-${x}`).join(' ');
  // TL;DR: relative urls don't work well, so manually create the absolute url to the parent
  const dirArr = location.pathname.split('/')
  dirArr.pop()
  const upDir = dirArr.join('/')

  const albumContents = contents?.edges?.map(({ node }) => node) || [];
  return (
    <AppContext.Provider value={{ ratingsVisible, toggleRating }}>
      <div className="AlbumPage Page">
        <div className="Page--LeftRail">
          <RatingMenu
            ref={ratingMenu}
            images={albumContents} />
        </div>
        <div className="Page--Main">
          <h2>{path || 'Home'} {path && <small>« <a className="breadcrumb" href={upDir}>go back</a></small>}</h2>
          <div className={`AlbumPage--flex-container ${visibleRatingsClass}`}>
            {albumContents.map((node) => (
              <div className={`AlbumPage--tile rating-${node?.xmp?.rating}`}>
                {node.__typename === 'Album' && <AlbumThumb album={node} />}
                {node.__typename === 'Image' && <Thumbnail image={node} />}
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppContext.Provider>
  );
}

export default AlbumPage;
