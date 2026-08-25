// ArtworkDetail.jsx

import { useParams } from "react-router-dom"

function ArtworkDetail() {
    let { artworkId } = useParams();
    return <h1>Artwork Detail {artworkId}</h1>;
}

export default ArtworkDetail;