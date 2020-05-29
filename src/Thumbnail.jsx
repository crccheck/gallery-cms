import { h } from 'preact'
import { useState } from 'preact/hooks'

import { query } from './graphql'

const SET_IMAGE_RATING_MUTATION = `
mutation SetImageRating($input: SetRatingInput!) {
  setRating(input: $input) {
    image {
      xmp {
        rating
      }
    }
  }
}
`

function Thumbnail({ image }) {
  const [rating, setRatingUI] = useState(image.xmp.rating)

  const setRating = async (image, newRating) => {
    const { data, errors } = await query(SET_IMAGE_RATING_MUTATION, { input: { path: image.path, rating: newRating } })
    if (errors) {
      console.error(errors)
      return
    }
    // HACK update `image` prop state
    image.xmp.rating = data.setRating.image.xmp.rating
    setRatingUI(data.setRating.image.xmp.rating)
  }
  const width = 500
  const height = width * image.attributes.height / image.attributes.width
  return (<div className="Thumbnail">
    <img src={image.thumb} loading="lazy" alt={image.iptc.caption} width={width} height={height}></img>
    <div className="Thumbnail--overlay">
      <p className="Thumbnail--caption">{image.iptc.caption}</p>
      <ul className="Thumbnail--keywords">
        {image.iptc.keywords.map((keyword) => <li>{keyword}</li>)}
      </ul>
      <div className="Thumbnail--rating" title="Image rating" onMouseLeave={() => setRatingUI(image.xmp.rating)}>
        {[1, 2, 3, 4, 5].map((x) =>
          <span
            onClick={() => x != image.xmp.rating && setRating(image, x)}
            onMouseOver={() => setRatingUI(x)}
          >{x <= rating ? '★' : '☆'}</span>
        )}
      </div>
    </div>
  </div>
  )
}

export default Thumbnail
