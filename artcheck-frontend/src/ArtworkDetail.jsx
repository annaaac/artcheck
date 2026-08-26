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
      setMatches(data.matches); // pull the array out of the response object
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadMatches();
  }, [artworkId]); // re-fetch if the user navigates between different artworks

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
          {matches.map((match, i) => (
            <li key={i}>
              <a href={match.url} target="_blank" rel="noreferrer">
                {match.url}
              </a>{" "}
              — {match.similarity_score}%
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

export default ArtworkDetail;