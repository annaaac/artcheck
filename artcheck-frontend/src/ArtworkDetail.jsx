import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

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
            <section id="left">
                <Link to="/">
                    Back to Gallery
                </Link>
            </section>

            <section id="center">
                <h1>Artwork Detail {artworkId}</h1>
                <img
                    src={`http://localhost:8000/artworks/${artworkId}/image`}
                    alt={`Artwork ${artworkId}`}
                    width={300}
                />

                <button className="delete-button" onClick={() => deleteArtwork()}>
                    DELETE
                </button>
            </section>

            <section id="right">
                <h2>Matches found</h2>
                {error && <p className="error">{error}</p>}
                {matches.length === 0 && <p>No matches found yet.</p>}
                <ul>
                    {matches.map((match) => (
                        <li key={match.id}>
                            <a href={match.url} target="_blank" rel="noreferrer">
                                <img src={match.url} alt="Description of the image" height="100"></img>
                            </a>{" "}
                            <p>{match.similarity_score}%
                                {match.status === "new" && <span className="badge"> ● new</span>}</p>
                            <button onClick={() => dismissMatch(match.id)}>
                                Dismiss
                            </button>
                        </li>
                    ))}
                </ul>
            </section>
        </>
    );
}

export default ArtworkDetail;