import { h } from 'preact'

function Thumbnail({ image }) {
  // TODO get image width/height/AR
  console.log(image.iptc.keywords)
  return (<div className="Thumbnail">
    <img src={image.thumb} loading="lazy" alt="…" width="200" height="200"></img>
    <div className="Thumbnail--overlay">
      <p className="Thumbnail--caption">{image.iptc.caption}</p>
      <ul className="Thumbnail--keywords">
        {image.iptc.keywords.map((keyword) => <li>{keyword}</li>)}
      </ul>
    </div>
  </div>
  )
}

export default Thumbnail
