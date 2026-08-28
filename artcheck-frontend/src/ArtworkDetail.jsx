import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";

function ArtworkDetail() {
  const { artworkId } = useParams();
  const [matches, setMatches] = useState([]);
  const [error, setError] = useState(null);

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

  useEffect(() => {
    loadMatches();
  }, [artworkId]);

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

  return (
    <>
      <section id="center">
        <h1>Artwork Detail {artworkId}</h1>
        <img
          src={`http://localhost:8000/artworks/${artworkId}/image`}
          alt={`Artwork ${artworkId}`}
          width={300}
        />
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
                Dismiss as false positive
              </button>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

export default ArtworkDetail;