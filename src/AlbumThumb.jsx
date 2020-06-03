import { h } from 'preact';
import { Link } from 'preact-router/match';
import './AlbumThumb.scss';

export default function AlbumThumb({ album }) {
  const smallWidth = album.thumbs.small.size;
  const mediumWidth = album.thumbs.medium.size;
  return (
    <div className="AlbumThumb">
      <Link href={`/album/${album.path}`}>
        <img
          src={album.thumbs.small.src}
          srcset={`${album.thumbs.small.src} ${smallWidth}w, ${album.thumbs.medium.src} ${mediumWidth}w`}
          loading="lazy"
          alt={album.path}
          width={500}
          height={500}
        />
      </Link>
      <Link href={`/album/${album.path}`} className="title">{album.path}</Link>
    </div>
  );
}
