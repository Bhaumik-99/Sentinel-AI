import { useEffect, useState } from 'react'
import { Activity, ArrowUpRight, Bot, CheckCircle2, Clock3, Database, FileVideo, Filter, Gauge, LoaderCircle, Mic, Search, ShieldCheck, UploadCloud, Video, Volume2, Trash2 } from 'lucide-react'

const API = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const fmt = n => Number(n || 0).toLocaleString()
const time = s => String(Math.floor(Number(s || 0) / 60)).padStart(2, '0') + ':' + String(Math.floor(Number(s || 0) % 60)).padStart(2, '0')

export default function App() {
  const [videos, setVideos] = useState([])
  const [events, setEvents] = useState([])
  const [selected, setSelected] = useState('')
  const [label, setLabel] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [apiOnline, setApiOnline] = useState(false)

  async function loadVideos() {
    try {
      const r = await fetch(API + '/api/videos')
      if (!r.ok) throw new Error('API unavailable')
      const d = await r.json()
      setVideos(d.items || [])
      setApiOnline(true)
    } catch { setApiOnline(false) }
  }
  async function loadEvents() {
    try {
      const p = new URLSearchParams({ limit: '150' })
      if (selected) p.set('video_id', selected)
      if (label.trim()) p.set('label', label.trim())
      const r = await fetch(API + '/api/events?' + p)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Could not load events')
      setEvents(d.items || [])
    } catch (e) { setError(e.message) }
  }
  useEffect(() => { loadVideos() }, [])
  useEffect(() => { loadEvents() }, [selected, label, videos])

  async function upload() {
    if (!file) return
    setBusy(true); setError(''); setNotice(''); setAnswer(null)
    const data = new FormData(); data.append('file', file)
    try {
      const r = await fetch(API + '/api/videos', { method: 'POST', body: data })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Video processing failed')
      setNotice('Processed ' + d.filename + ': ' + d.processed_frames + ' sampled frames in ' + d.processing_seconds + 's.')
      setFile(null)
      const input = document.getElementById('video-input'); if (input) input.value = ''
      await loadVideos()
      setSelected(String(d.video_id))
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  function startVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('Voice input is not supported in this browser. Try a recent version of Chrome or Edge.')
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = event => setQuestion(event.results[0][0].transcript)
    recognition.onerror = () => setError('Voice input failed. Check microphone permission and try again.')
    recognition.start()
  }
  function speakAnswer() {
    if (!answer?.answer || !('speechSynthesis' in window)) {
      setError('Speech output is not supported in this browser.')
      return
    }
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(answer.answer))
  }
  async function removeVideo(video) {
    if (!window.confirm('Delete ' + video.filename + ' and its stored detections?')) return
    setError('')
    try {
      const r = await fetch(API + '/api/videos/' + video.id, { method: 'DELETE' })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Could not delete video')
      if (String(video.id) === selected) setSelected('')
      await loadVideos()
      setNotice('Deleted ' + video.filename + ' and its event records.')
    } catch (e) { setError(e.message) }
  }
  async function ask() {
    if (!question.trim()) return
    setBusy(true); setError(''); setAnswer(null)
    try {
      const r = await fetch(API + '/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, video_id: selected ? Number(selected) : null }) })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Question failed')
      setAnswer(d)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><ShieldCheck size={22}/></div><div><strong>sentinel<span>.ai</span></strong><small>VIDEO INTELLIGENCE</small></div></div>
      <div className="side-label">WORKSPACE</div>
      <button className="nav-item active"><Video size={17}/> Overview <span className="nav-dot"/></button>
      <button className="nav-item" onClick={() => document.getElementById('events')?.scrollIntoView({behavior:'smooth'})}><Activity size={17}/> Event explorer</button>
      <button className="nav-item" onClick={() => document.getElementById('agent')?.scrollIntoView({behavior:'smooth'})}><Bot size={17}/> Ask Sentinel</button>
      <div className="sidebar-bottom"><div className={'connection ' + (apiOnline ? 'online' : '')}><span/>{apiOnline ? 'API connected' : 'Waiting for API'}</div><p>Local-first video analytics prototype.</p><span className="version">BUILD 0.1.0</span></div>
    </aside>
    <main className="main">
      <header className="topbar"><div><span className="breadcrumb">Workspace /</span> <strong>Overview</strong></div><div className="top-actions"><span className="live-pill"><span/> SYSTEM STATUS</span><span className="avatar">S</span></div></header>
      <section className="welcome"><div><div className="eyebrow"><span className="eyebrow-line"/> INTELLIGENCE CONSOLE</div><h1>See beyond the <em>frame.</em></h1><p>Turn recorded video into searchable, timestamped evidence.</p></div><div className="welcome-icon"><Video size={30}/><span/></div></section>
      {error && <div className="alert error">{error}<button onClick={() => setError('')}>Dismiss</button></div>}
      {notice && <div className="alert success"><CheckCircle2 size={17}/>{notice}<button onClick={() => setNotice('')}>Dismiss</button></div>}
      <section className="stats-grid">
        <Stat icon={<FileVideo/>} label="VIDEOS PROCESSED" value={videos.length} sub="Uploaded to this workspace"/>
        <Stat icon={<Database/>} label="EVENT RECORDS" value={events.length} sub="Current event filter"/>
        <Stat icon={<Gauge/>} label="SAMPLED FRAMES" value={fmt(videos.reduce((n,v) => n + Number(v.processed_frames || 0), 0))} sub="Across processed videos"/>
        <Stat icon={<Activity/>} label="PROCESSING RUNS" value={videos.length} sub="Model inference jobs"/>
      </section>
      <section className="content-grid">
        <div className="panel upload-panel">
          <div className="panel-heading"><div><div className="section-kicker">INGESTION</div><h2>Analyze a video</h2></div><span className="icon-chip"><UploadCloud size={19}/></span></div>
          <p className="muted">Upload a clip to detect and track objects, then search the resulting event timeline.</p>
          <label className="dropzone" htmlFor="video-input"><input id="video-input" type="file" accept="video/mp4,video/quicktime,video/x-msvideo,video/webm,.mkv" onChange={e => setFile(e.target.files?.[0] || null)}/><span className="upload-icon"><UploadCloud size={24}/></span><strong>{file ? file.name : 'Drop a video here or browse'}</strong><small>{file ? (file.size / 1024 / 1024).toFixed(1) + ' MB selected' : 'MP4, MOV, AVI, MKV or WEBM · Max 250 MB'}</small></label>
          <button className="primary-btn" onClick={upload} disabled={!file || busy}>{busy ? <LoaderCircle className="spin" size={17}/> : <Activity size={17}/>} {busy ? 'Processing video…' : 'Run detection pipeline'} <ArrowUpRight size={16}/></button>
          <div className="pipeline-note"><span className="mini-status"/> YOLO detection <span className="note-sep">·</span> ByteTrack <span className="note-sep">·</span> SQLite event store</div>
        </div>
        <div className="panel agent-panel" id="agent">
          <div className="panel-heading"><div><div className="section-kicker">NATURAL LANGUAGE</div><h2>Ask Sentinel</h2></div><span className="icon-chip purple"><Bot size={19}/></span></div>
          <p className="muted">Ask about objects detected in your footage. Answers are grounded in stored detections, not generated scene guesses.</p>
          <div className="question-box"><Search size={18}/><input value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => e.key === 'Enter' && ask()} placeholder="e.g. When was a person detected?"/><button className="voice-btn" onClick={startVoiceInput} title="Ask by voice" aria-label="Ask by voice"><Mic size={16}/></button><button onClick={ask} disabled={busy || !question.trim()} aria-label="Ask"><ArrowUpRight size={18}/></button></div>
          <div className="suggestions"><span>TRY:</span>{['person', 'car', 'dog'].map(q => <button key={q} onClick={() => setQuestion('When was ' + q + ' detected?')}>{q}</button>)}</div>
          {answer && <div className="answer-card"><div className="answer-label"><CheckCircle2 size={15}/> EVIDENCE-BASED RESPONSE <button className="speak-btn" onClick={speakAnswer} title="Read answer aloud"><Volume2 size={14}/></button></div><p>{answer.answer}</p><small>{answer.method}</small>{answer.evidence?.length > 0 && <div className="evidence-list">{answer.evidence.slice(0,4).map(e => <div key={e.event_id}><span>{e.label}</span><strong>{time(e.timestamp_seconds)}</strong><small>{Math.round(e.confidence*100)}% confidence</small></div>)}</div>}</div>}
        </div>
      </section>
      <section className="panel event-panel" id="events">
        <div className="panel-heading event-heading"><div><div className="section-kicker">OBSERVABILITY</div><h2>Event explorer <span className="count-badge">{events.length}</span></h2></div><div className="filters"><div className="filter-control"><Filter size={15}/><select value={selected} onChange={e => setSelected(e.target.value)}><option value="">All videos</option>{videos.map(v => <option value={v.id} key={v.id}>#{v.id} · {v.filename}</option>)}</select></div><div className="filter-control"><Search size={15}/><input placeholder="Filter label…" value={label} onChange={e => setLabel(e.target.value)}/></div></div></div>
        <div className="table-wrap"><table><thead><tr><th>EVENT</th><th>VIDEO</th><th>TIMESTAMP</th><th>CONFIDENCE</th><th>TRACK ID</th><th>FRAME</th></tr></thead><tbody>
          {events.slice(0,100).map(e => <tr key={e.id}><td><span className="event-name"><span className="event-dot"/>{e.label}</span></td><td><span className="video-ref">VID-{String(e.video_id).padStart(3,'0')}</span></td><td><span className="timestamp"><Clock3 size={14}/>{time(e.timestamp_seconds)}</span></td><td><div className="confidence"><span><i style={{width:Math.max(0,Math.min(100,e.confidence*100)) + '%'}}/></span><b>{(e.confidence*100).toFixed(1)}%</b></div></td><td className="mono">{e.track_id ?? '—'}</td><td className="mono">{e.frame_number}</td></tr>)}
          {!events.length && <tr><td colSpan="6"><div className="empty-state"><Database size={25}/><strong>No events to display</strong><span>Upload a video or clear your filters.</span></div></td></tr>}
        </tbody></table></div>
        <div className="table-footer"><span>Showing {Math.min(events.length,100)} of {events.length} returned records</span><span><span className="mini-status"/> Updated from local event store</span></div>
      </section>
      <footer><span>© 2026 SENTINEL AI</span><span>BUILT FOR EXPERIMENTATION · NOT FOR HIGH-STAKES DECISIONS</span></footer>
    </main>
  </div>
}
function Stat({icon,label,value,sub}) { return <div className="stat-card"><div className="stat-top"><span>{label}</span><span className="stat-icon">{icon}</span></div><strong>{value}</strong><small>{sub}</small></div> }
