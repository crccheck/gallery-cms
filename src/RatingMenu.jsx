import { h } from 'preact';
import { useContext } from 'preact/hooks';

import AppContext from './AppContext';

import './RatingMenu.scss';

function RatingMenu() {
  const { ratingsVisible, toggleRating } = useContext(AppContext);
  return (
    <div className="RatingMenu">
      Rating
      <ul>
        {['5', '4', '3', '2', '1', '0'].map((rating) => (
          <li
            className={ratingsVisible.has(rating) ? 'active' : ''}
            onClick={() => toggleRating(rating)}
          >
            {rating}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default RatingMenu;
