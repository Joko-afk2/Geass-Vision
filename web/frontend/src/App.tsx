import { ChessGame } from "./components/ChessGame";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header className="entete">
        <h1>Moteur d&apos;échecs</h1>
        <p>Humain vs moteur — interface web</p>
      </header>
      <main>
        <ChessGame />
      </main>
    </div>
  );
}
