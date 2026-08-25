//App.jsx

import { BrowserRouter, Routes, Route } from "react-router-dom";
import Gallery from "./Gallery";
import ArtworkDetail from "./ArtworkDetail";

import './App.css'

function App() {
    return (
        <>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Gallery />} />
                    <Route path="/artworks/:artworkId" element={<ArtworkDetail />} />
                </Routes>
            </BrowserRouter>
        </>
    )
}


export default App
