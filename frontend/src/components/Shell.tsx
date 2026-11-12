import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAppData } from '../state/AppData'
import ui from '../styles/ui.module.css'
import styles from './Shell.module.css'
import { Tag } from './Tag'

const PLANNED = ['Activities', 'Saved decisions', 'Plugins', 'Search', 'History']

const READY_STATES = new Set(['ready', 'configured', 'connected'])

export function Shell() {
  const { runs, system, error } = useAppData()

  return (
    <div className={styles.app}>
      <nav className={styles.sidebar} aria-label="Primary">
        <div className={styles.brand}>
          <span className={styles.mark}>[ ]</span> Context Engine
        </div>
        <Link className={`${ui.btn} ${ui.primary} ${styles.newRun}`} to="/runs">
          + New run
        </Link>
        <ul className={styles.nav}>
          <li>
            <NavLink to="/runs" className={({ isActive }) => (isActive ? styles.active : '')}>
              Runs
            </NavLink>
          </li>
          <li>
            <NavLink to="/knowledge" className={({ isActive }) => (isActive ? styles.active : '')}>
              Knowledge
            </NavLink>
          </li>
        </ul>

        <div className={styles.section}>
          <span className={ui.eyebrow}>Runs this session</span>
          <ul className={styles.nav} aria-label="Runs this session">
            {runs.length === 0 && <li className={styles.empty}>No runs yet</li>}
            {runs.map((run) => (
              <li key={run.run_id}>
                <NavLink
                  to={`/runs/${run.run_id}`}
                  className={({ isActive }) => (isActive ? styles.active : '')}
                >
                  <span className={styles.runTitle}>{run.prompt}</span>
                  <span className={styles.sub}>{run.status.replace('_', ' ')}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.section}>
          <span className={ui.eyebrow}>Not built yet</span>
          <ul className={styles.nav}>
            {PLANNED.map((name) => (
              <li key={name} className={styles.planned}>
                <span>{name}</span>
                <Tag tone="planned">Planned</Tag>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.foot} aria-label="Dependency status">
          {system?.dependencies.map((dependency) => (
            <div key={dependency.name}>
              <span>
                <span className={READY_STATES.has(dependency.state) ? styles.dot : styles.dotBad} />
                {dependency.name}
              </span>
              <span>{dependency.state}</span>
            </div>
          ))}
          {!system && <div>{error ? 'API unavailable' : 'Loading…'}</div>}
        </div>
      </nav>
      <Outlet />
    </div>
  )
}
