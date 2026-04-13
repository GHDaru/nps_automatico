import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Avaliacao from './pages/Avaliacao'
import AvaliacaoPersonalizada from './pages/AvaliacaoPersonalizada'
import PromptManager from './pages/PromptManager'
import CamposManager from './pages/CamposManager'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Avaliacao />} />
            <Route path="/avaliacao-personalizada" element={<AvaliacaoPersonalizada />} />
            <Route path="/prompts" element={<PromptManager />} />
            <Route path="/campos" element={<CamposManager />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
