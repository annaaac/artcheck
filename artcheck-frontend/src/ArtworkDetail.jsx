import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

import './ArtworkDetail.css'

function ArtworkDetail() {
    const { artworkId } = useParams();
    const [matches, setMatches] = useState([]);
    const [error, setError] = useState(null);


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
        loadMatches();

        function handleVisibilityChange() {
            if (document.visibilityState === "visible") {
                fetch(`http://localhost:8000/artworks/${artworkId}/mark-reviewed`, {
                    method: "POST",
                }).catch(() => { });
            }
        }

        document.addEventListener("visibilitychange", handleVisibilityChange);

        return () => {
            document.removeEventListener("visibilitychange", handleVisibilityChange);
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
                    <img
                        src={`http://localhost:8000/artworks/${artworkId}/image`}
                        alt={`Artwork ${artworkId}`}
                    />
                    <p>id: {artworkId}</p>
                    <br></br>
                    <button className="delete-button" onClick={() => deleteArtwork()}>
                        DELETE
                    </button>
                </div>

                <div id="detail-right">
                    <h2>Matches found</h2>
                    {error && <p className="error">{error}</p>}
                    {matches.length === 0 && <p>No matches found yet.</p>}

                    <div className="matches-container">
                        {matches.map((match) => (

                            <div key={match.id} className="match-item">
                                <div>
                                    <a href={match.url} target="_blank" rel="noreferrer">
                                        <img src={match.url} alt="Match preview" onError={(e) => { e.target.style.visibility = "hidden"; }} />
                                    </a><br></br>
                                    {/* TODO: BRING DISMISSED MATCHES BACKK. undo button? */}
                                    <button onClick={() => dismissMatch(match.id)}>
                                        Not a match
                                    </button>
                                </div>

                                <div className="match-text">
                                    <p align="left">
                                        similarity: {match.similarity_score}%<br></br>
                                        url: <a href={match.url} target="_blank" rel="noreferrer">{match.url}</a><br></br>
                                        Found on {match.time_scanned}<br></br>
                                        {match.status === "new" && <span className="badge"> ● new</span>}</p>


                                </div>

                            </div>

                        ))}
                    </div>

                </div>
            </div>
        </>
    );
}

export default ArtworkDetail;