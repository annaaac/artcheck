import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

import './ArtworkDetail.css'

function ArtworkDetail() {
    // BUG: image preview incorrect. cachebust.
    const { artworkId } = useParams();
    const [artwork, setArtwork] = useState();
    const [matches, setMatches] = useState([]);
    const [error, setError] = useState(null);

    async function loadArtwork() {
        try {
            const response = await fetch(`http://localhost:8000/artworks/${artworkId}`);
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            const data = await response.json();
            setArtwork(data);
        } catch (err) {
            setError(err.message);
        }
    }

    async function deleteArtwork() {
        try {
            const response = await fetch(`http://localhost:8000/artworks/${artworkId}`, {
                method: "DELETE",
            });
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            window.location.href = "/";
        } catch (err) {
            setError(err.message);
        }
    }


    async function loadMatches() {
        try {
            const response = await fetch(`http://localhost:8000/artworks/${artworkId}/scan`);
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            const data = await response.json();
            setMatches(data.matches);
        } catch (err) {
            setError(err.message);
        }
    }


    async function dismissMatch(matchId) {
        try {
            const response = await fetch(`http://localhost:8000/matches/${matchId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: "dismissed" }),
            });
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            await loadMatches(); // refetch so the dismissed row disappears
        } catch (err) {
            setError(err.message);
        }
    }


    useEffect(() => {
        loadArtwork();
        loadMatches();

        return () => {
            fetch(`http://localhost:8000/artworks/${artworkId}/mark-reviewed`, {
                method: "POST",
            }).catch(() => { });
        };
    }, [artworkId]);


    return (
        <>
            {/* <section id="top-bar">
                <Link to="/">
                    Back to Gallery
                </Link>
            </section> */}


            <div className="detail-container">
                <div id="detail-left">
                    {artwork && (
                        <img
                            src={`http://localhost:8000/artworks/${artworkId}/image?v=${artwork.time_uploaded}`}
                            alt={`Artwork ${artworkId}`}
                        />
                    )}
                    <p>id: {artworkId}</p>
                    <br></br>
                    <button className="delete-button" onClick={() => deleteArtwork()}>
                        DELETE
                    </button>
                </div>

                <div id="detail-right">
                    <h2>{matches.length === 0 ? "No" : matches.length} matches found</h2>
                    {error && <p className="error">{error}</p>}

                    <div className="matches-container">
                        {matches.map((match) => (

                            <div key={match.id} className="match-item">
                                <div>
                                    <a href={match.url} target="_blank" rel="noreferrer">
                                        <img src={match.url} alt="Match preview" onError={(e) => { e.target.style.visibility = "hidden"; }} />
                                    </a><br></br>
                                    {/* TODO: BRING DISMISSED MATCHES BACKK. undo button? 
                                    DO NOT PLAY GIFS INSTEAD LABEL THEM AS GIFS */}
                                </div>

                                <div className="match-text">
                                    <p align="left">
                                        similarity: {match.similarity_score}%<br></br>
                                        url: <a href={match.url} target="_blank" rel="noreferrer">{match.url}</a><br></br>
                                        Found on {new Date(match.time_scanned).toLocaleString(navigator.language, {
                                            dateStyle: "long",
                                            timeStyle: "long"
                                        })}<br></br>
                                        {match.status === "new" && <span className="badge"> ● new</span>}</p>


                                </div>

                                <button onClick={() => dismissMatch(match.id)}>
                                    Not a match
                                </button>

                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </>
    );
}

export default ArtworkDetail;