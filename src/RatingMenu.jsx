import { h } from 'preact';
import { useContext } from 'preact/hooks';

import AppContext from './AppContext';

import './RatingMenu.scss';

function RatingMenu({ images }) {
  const { ratingsVisible, toggleRating } = useContext(AppContext);
  const ratingCounts = new Map([
    ['5', 0],
    ['4', 0],
    ['3', 0],
    ['2', 0],
    ['1', 0],
    ['0', 0],
    ['-1', 0],
  ]);
  images && images.forEach((image) => {
    ratingCounts.set('' + image.xmp.rating,
      ratingCounts.get('' + image.xmp.rating) + 1
    )
  })
  console.log(ratingCounts)
  return (
    <div className="RatingMenu">
      Rating
      <ul>
        {['5', '4', '3', '2', '1', '0'].map((rating) => (
          <li
            className={ratingsVisible.has(rating) ? 'active' : ''}
            onClick={() => toggleRating(rating)}
          >
            {rating} <small>{ratingCounts.get(rating)}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default RatingMenu;
