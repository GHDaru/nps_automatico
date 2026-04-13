import { NavLink } from 'react-router-dom'
import './Sidebar.css'

const navItems = [
  { to: '/', label: '📊 Avaliação', end: true },
  { to: '/avaliacao-personalizada', label: '🎯 Avaliação Personalizada' },
  { to: '/prompts', label: '📝 Prompts' },
  { to: '/campos', label: '🗂️ Campos Extraídos' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand-icon">🤖</span>
        <span className="sidebar-brand-text">NPS Automático</span>
      </div>
      <nav className="sidebar-nav">
        {navItems.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              'sidebar-link' + (isActive ? ' sidebar-link--active' : '')
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
