import { ChessGame } from "./components/ChessGame";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header className="entete">
        <div className="entete-marque">
          <img src="/geass-logo.png" alt="Geass" className="logo-geass" />
          <div className="entete-titres">
            <h1>Geass Vision</h1>
            <p>Affronte le moteur — interface web</p>
          </div>
        </div>
      </header>
      <main>
        <ChessGame />
      </main>
      <footer className="pied">
        <span>Auteur : Joko</span>
        <a
          href="https://github.com/Joko-afk2"
          target="_blank"
          rel="noreferrer"
        >
          GitHub : Joko-afk2
        </a>
        <span>Discord : Joko8099</span>
      </footer>
    </div>
  );
}
