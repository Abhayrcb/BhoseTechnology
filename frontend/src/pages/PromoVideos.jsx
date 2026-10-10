import { useEffect, useState } from "react";
import { ExternalLink, PlayCircle } from "lucide-react";
import { api } from "../lib/api";
import { Shell } from "../components/Shell";

const youtubeEmbedUrl = url => {
  const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|shorts\/|embed\/))([\w-]{11})/);
  return match ? `https://www.youtube.com/embed/${match[1]}` : null;
};

const VideoCard = ({ video }) => {
  const embed = video.platform === "YouTube" ? youtubeEmbedUrl(video.video_url) : null;
  return <div className="product-card video-promo-card" data-testid={`promo-video-card-${video.video_id}`}>
    {embed ? <div className="video-embed"><iframe src={embed} title={video.title} loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen data-testid={`promo-video-embed-${video.video_id}`}/></div>
      : <a className="video-embed video-embed-link" href={video.video_url} target="_blank" rel="noreferrer" data-testid={`promo-video-open-${video.video_id}`}><PlayCircle size={44}/><span>Watch on {video.platform}</span></a>}
    <div className="product-info">
      <div className="product-meta"><span>{video.platform}</span></div>
      <h3 data-testid={`promo-video-title-${video.video_id}`}>{video.title}</h3>
      {video.description && <p data-testid={`promo-video-description-${video.video_id}`}>{video.description}</p>}
      <a className="video-external-link" href={video.video_url} target="_blank" rel="noreferrer" data-testid={`promo-video-link-${video.video_id}`}>Open original link <ExternalLink size={15}/></a>
    </div>
  </div>;
};

export default function PromoVideos({ cartCount }) {
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    api.get("/promo-videos").then(r => { if (active) setVideos(r.data); }).catch(() => { if (active) setError("Videos could not be loaded. Please try again shortly."); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  return <Shell cartCount={cartCount}><main>
    <section className="collection" id="videos">
      <div className="section-heading"><div><p className="eyebrow">FOLLOW ALONG</p><h2 data-testid="promo-videos-title">Our latest videos.</h2></div><p className="muted">See the laptops in action<br/>on our social channels.</p></div>
      {error && <p className="error-message" data-testid="promo-videos-error" role="alert">{error}</p>}
      {loading ? <p className="loading" data-testid="promo-videos-loading">Loading videos…</p> : <>
        <div className="product-grid video-grid">{videos.map(v => <VideoCard key={v.video_id} video={v}/>)}</div>
        {!videos.length && !error && <div className="empty" data-testid="promo-videos-empty">No videos posted yet. Check back soon.</div>}
      </>}
    </section>
  </main></Shell>;
}
