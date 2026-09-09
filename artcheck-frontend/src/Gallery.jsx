import { useState, useEffect, useRef } from 'react'
import { Link } from "react-router-dom"

function Gallery() {
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);
    const [artworks, setArtworks] = useState([]);
    const [error, setError] = useState(null);
    const [scanStatuses, setScanStatuses] = useState({}); // { [artworkId]: "scanning" }

    const pollIntervals = useRef({});

    async function loadArtworks() {
        try {
            const response = await fetch("http://localhost:8000/artworks");
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            const data = await response.json();
            setArtworks(data);
        } catch (err) {
            setError(err.message);
        }
    }

    useEffect(() => {
        loadArtworks();

        return () => {
            // Clear all polling intervals when the component unmounts
            Object.values(pollIntervals.current).forEach(clearInterval);
        };
    }, []);

    function pollScanStatus(artworkId) {
        let attempts = 0;
        const interval = setInterval(async () => {
            attempts++;
            try {
                const response = await fetch(`http://localhost:8000/artworks/${artworkId}/scan`);
                const data = await response.json();

                if (data.matches.length > 0 || attempts >= 8) {
                    clearInterval(interval);
                    setScanStatuses((prev) => {
                        const updated = { ...prev };
                        delete updated[artworkId]; // remove "scanning" - real counts take over from artworks list
                        return updated;
                    });
                    loadArtworks(); // Refresh the artworks list to show new matches
                }
            } catch (err) {
                clearInterval(interval);
                delete pollIntervals.current[artworkId];
            }
        }, 4000); // Poll every 5 seconds
        pollIntervals.current[artworkId] = interval;
    }

    async function handleSubmit() {
        setError(null);
        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch("http://localhost:8000/artworks?user_id=anna", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }

            const data = await response.json();
            setResult(data);
            setFile(null);
            await loadArtworks(); // Refresh the artworks list to include the newly uploaded artwork

            // Start polling for scan status
            setScanStatuses((prev) => ({ ...prev, [data.id]: "scanning" }));
            await fetch(`http://localhost:8000/artworks/${data.id}/scan`, { method: "POST" });
            pollScanStatus(data.id);
        } catch (err) {
            setError(err.message);
        }
    }

    return (
        <>
            <section id="center">
                <div>
                    <h1>Gallery page</h1>
                    <h2>Welcome to Artcheck</h2>
                    <p>Upload an artwork!</p>
                </div>
                <input
                    type="file"
                    accept="image/png, image/jpeg"
                    onChange={(e) => setFile(e.target.files[0])}
                />
                <button className="button" type="button" onClick={handleSubmit}>
                    Submit
                </button>
                {error && <p className="error">{error}</p>}
            </section>

            <section id="right">
                <h2>Artworks</h2>
                <div class="container">
                    {artworks.map((artwork) => (
                        <Link to={`/artworks/${artwork.id}`} key={artwork.id} className="link">
                            <img
                                src={`http://localhost:8000/artworks/${artwork.id}/image`}
                                alt={artwork.filename}
                                width={120}
                            />
                            <div>
                                {scanStatuses[artwork.id] === "scanning" ? (
                                    <div className="status">Pending…</div>
                                ) : artwork.match_count > 0 ? (
                                    <div className="status">{artwork.match_count} match{artwork.match_count === 1 ? "" : "es"}</div>
                                ) : (
                                    <div className="status">Clear</div>
                                )}
                                {artwork.new_match_count > 0 && (
                                    <div className="badge">●</div>
                                )}
                            </div>
                        </Link>
                    ))}
                </div>
            </section>
        </>
    );
}

export default Gallery;