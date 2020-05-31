import { h } from 'preact';
import { Link } from 'preact-router/match';
import './AlbumThumb.scss';

export default function AlbumThumb({ album }) {
  return (
    <div className="AlbumThumb">
      <Link href={`/album/${album.path}`}><div className="placeholder">{album.path}</div></Link>
      <Link href={`/album/${album.path}`} className="title">{album.path}</Link>
    </div>
  );
}
