import React from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity, AlertCircle, ArrowDownRight, ArrowRight, BookOpen, Check,
  CheckCircle2, ChevronDown, CircleHelp, ClipboardCheck, Database, FileText,
  FlaskConical, Gauge, Layers3, LoaderCircle, Menu, MessageSquareText,
  RefreshCw, Search, ShieldCheck, SlidersHorizontal, Sparkles, Target,
  UploadCloud, XCircle,
} from 'lucide-react'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const LABELS = [
  { key: 'supported', title: 'Supported', tone: 'green', detail: 'Evidence supports the claim' },
  { key: 'contradicted', title: 'Contradicted', tone: 'red', detail: 'Evidence conflicts with the claim' },
  { key: 'partially_supported', title: 'Partially supported', tone: 'amber', detail: 'Only part of the claim is supported' },
  { key: 'insufficient_evidence', title: 'Insufficient evidence', tone: 'slate', detail: 'Evidence is not enough to decide' },
]
const pct = value => value === null || value === undefined || !Number.isFinite(value) ? '—' : `${(value * 100).toFixed(1)}%`
const human = value => value?.replaceAll('_', ' ') || 'Unknown'

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof body.detail === 'string' ? body.detail : body.detail?.message || JSON.stringify(body.detail || body)
    throw new Error(detail || `Request failed (${response.status})`)
  }
  return body
}

function Badge({ status, children }) {
  const tone = LABELS.find(x => x.key === status)?.tone || 'slate'
  return <span className={`badge ${tone}`}>{children || human(status)}</span>
}
function MetricCard({ icon: Icon, label, value, hint, tone = '' }) {
  return <article className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={18} /></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-hint">{hint}</div></article>
}
function PanelTitle({ eyebrow, title, description, action }) {
  return <div className="panel-title"><div><div className="eyebrow">{eyebrow}</div><h2>{title}</h2>{description && <p>{description}</p>}</div>{action}</div>
}
function Empty({ icon: Icon = Database, title, text }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={22} /></div><strong>{title}</strong><p>{text}</p></div>
}

export default function App() {
  const [page, setPage] = useState('overview')
  const [mobileNav, setMobileNav] = useState(false)
  const [health, setHealth] = useState(null)
  const [documents, setDocuments] = useState(null)
  const [evalStatus, setEvalStatus] = useState(null)
  const [evalReport, setEvalReport] = useState(null)
  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(5)
  const [askResult, setAskResult] = useState(null)
  const [askLoading, setAskLoading] = useState(false)
  const [evalLoading, setEvalLoading] = useState(false)
  const [reindexLoading, setReindexLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const refreshStatus = useCallback(async () => {
    try {
      const [h, d, e] = await Promise.all([api('/health'), api('/documents/status'), api('/evaluation/status')])
      setHealth(h); setDocuments(d); setEvalStatus(e); setError('')
    } catch (e) { setHealth(null); setError(e.message || 'Cannot connect to the backend.') }
  }, [])
  useEffect(() => { refreshStatus() }, [refreshStatus])

  const nav = [
    { id: 'overview', label: 'Overview', icon: Gauge, section: 'WORKSPACE' },
    { id: 'ask', label: 'Ask & verify', icon: MessageSquareText, section: 'WORKSPACE' },
    { id: 'evaluation', label: 'Evaluation lab', icon: FlaskConical, section: 'RESEARCH' },
    { id: 'documents', label: 'Document collection', icon: Layers3, section: 'RESEARCH' },
  ]
  const navigate = id => { setPage(id); setMobileNav(false); setError(''); setNotice('') }

  async function submitQuestion(event) {
    event.preventDefault(); if (!question.trim()) return
    setAskLoading(true); setError(''); setNotice(''); setAskResult(null)
    try { setAskResult(await api('/ask', { method: 'POST', body: JSON.stringify({ question: question.trim(), top_k: topK }) })) }
    catch (e) { setError(e.message || 'Could not verify this question.') }
    finally { setAskLoading(false) }
  }

  async function runEvaluation() {
    setEvalLoading(true); setError(''); setNotice(''); setEvalReport(null)
    try { const report = await api('/evaluation/run', { method: 'POST', body: JSON.stringify({ limit: 500 }) }); setEvalReport(report); setNotice(`Evaluation completed on ${report.evaluated_count} labelled examples.`); await refreshStatus() }
    catch (e) { setError(e.message || 'Evaluation could not run.') }
    finally { setEvalLoading(false) }
  }

  async function reindex() {
    setReindexLoading(true); setError(''); setNotice('')
    try { const result = await api('/documents/reindex', { method: 'POST' }); setNotice(`${result.message} Indexed ${result.page_count} pages and ${result.chunk_count} chunks.`); await refreshStatus() }
    catch (e) { setError(e.message || 'Could not rebuild the index.') }
    finally { setReindexLoading(false) }
  }

  const statusCounts = useMemo(() => {
    const counts = Object.fromEntries(LABELS.map(label => [label.key, 0]))
    for (const claim of askResult?.claims || []) if (claim.status in counts) counts[claim.status] += 1
    return counts
  }, [askResult])

  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav ? 'open' : ''}`}>
      <div className="brand"><div className="brand-mark"><ShieldCheck size={22} /></div><div><strong>EvidenceTrust<span> AI</span></strong><small>VERIFICATION WORKSPACE</small></div><button className="icon-button mobile-close" onClick={() => setMobileNav(false)} aria-label="Close menu"><XCircle size={19} /></button></div>
      <div className="workspace-pill"><div className={`status-dot ${health?.index_ready ? 'online' : ''}`} /><div><strong>{health?.index_ready ? 'Backend connected' : 'Backend unavailable'}</strong><small>{health?.index_ready ? 'Evidence index ready' : 'Start FastAPI to connect'}</small></div></div>
      {['WORKSPACE', 'RESEARCH'].map(section => <div className="nav-group" key={section}><div className="nav-heading">{section}</div>{nav.filter(item => item.section === section).map(item => <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => navigate(item.id)}><item.icon size={18} /><span>{item.label}</span>{item.id === 'evaluation' && evalStatus?.example_count > 0 && <span className="nav-count">{evalStatus.example_count}</span>}</button>)}</div>)}
      <div className="sidebar-bottom"><div className="research-note"><Sparkles size={16} /><strong>Research mode</strong><p>Only labelled, measured results belong in the paper.</p></div><div className="sidebar-foot"><span className="mini-dot" /> Local API <span className="foot-url">:8000</span></div></div>
    </aside>
    {mobileNav && <button className="scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}
    <main className="main-area">
      <header className="topbar"><button className="icon-button mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open menu"><Menu size={20} /></button><div className="breadcrumb">EvidenceTrust AI <ArrowRight size={14} /><strong>{nav.find(x => x.id === page)?.label}</strong></div><div className="topbar-right"><span className="env-label"><span className="mini-dot" /> LOCAL ENVIRONMENT</span><button className="icon-button" onClick={refreshStatus} title="Refresh status"><RefreshCw size={17} /></button><div className="avatar">ET</div></div></header>
      <div className="page-content">
        {error && <div className="alert error"><AlertCircle size={18} /><div><strong>Something needs attention</strong><p>{error}</p>{!health && <small>Backend URL: {API_BASE}</small>}</div><button onClick={() => setError('')} aria-label="Dismiss"><XCircle size={17} /></button></div>}
        {notice && <div className="alert success"><CheckCircle2 size={18} /><p>{notice}</p><button onClick={() => setNotice('')} aria-label="Dismiss"><XCircle size={17} /></button></div>}
        {page === 'overview' && <Overview health={health} documents={documents} evalStatus={evalStatus} onNavigate={navigate} onRefresh={refreshStatus} />}
        {page === 'ask' && <AskPage question={question} setQuestion={setQuestion} topK={topK} setTopK={setTopK} loading={askLoading} result={askResult} counts={statusCounts} onSubmit={submitQuestion} />}
        {page === 'evaluation' && <EvaluationPage status={evalStatus} report={evalReport} loading={evalLoading} onRun={runEvaluation} onRefresh={refreshStatus} />}
        {page === 'documents' && <DocumentsPage documents={documents} loading={reindexLoading} onReindex={reindex} onRefresh={refreshStatus} />}
        <footer className="page-footer"><span>EvidenceTrust AI · Research prototype</span><span>Evidence first. Claims second.</span></footer>
      </div>
    </main>
  </div>
}

function Overview({ health, documents, evalStatus, onNavigate, onRefresh }) {
  return <>
    <div className="hero"><div className="hero-copy"><div className="hero-kicker"><span className="hero-kicker-dot" /> EVIDENCE-GROUNDED VERIFICATION</div><h1>Trust the evidence.<br /><em>Verify every claim.</em></h1><p>Ask questions over your document collection, inspect claim-level reasoning, and measure verification quality with a labelled evaluation set.</p><div className="hero-actions"><button className="button primary" onClick={() => onNavigate('ask')}><MessageSquareText size={17} /> Ask a question <ArrowRight size={16} /></button><button className="button ghost-light" onClick={() => onNavigate('evaluation')}><FlaskConical size={17} /> Open evaluation lab</button></div></div><div className="hero-graphic"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="hero-shield"><ShieldCheck size={55} strokeWidth={1.35}/></div><div className="float-card float-top"><Check size={14}/> Evidence linked</div><div className="float-card float-bottom"><Activity size={14}/> Claim verification</div></div></div>
    <div className="section-heading"><div><div className="eyebrow">SYSTEM SNAPSHOT</div><h2>Your research workspace</h2></div><button className="text-button" onClick={onRefresh}><RefreshCw size={14}/> Refresh</button></div>
    <div className="metrics-grid"><MetricCard icon={ShieldCheck} label="Backend status" value={health?.index_ready ? 'Ready' : 'Offline'} hint={health?.index_ready ? 'API and index available' : 'Start the FastAPI server'} tone={health?.index_ready ? 'green' : 'red'}/><MetricCard icon={FileText} label="Indexed documents" value={documents?.document_count ?? '—'} hint={`${documents?.chunk_count ?? '—'} evidence chunks`} tone="blue"/><MetricCard icon={Database} label="Labelled examples" value={evalStatus?.example_count ?? '—'} hint={evalStatus?.example_count ? 'Ground-truth rows found' : 'Dataset needs labels'} tone="purple"/><MetricCard icon={ClipboardCheck} label="Evaluation state" value={evalStatus?.ready ? 'Ready' : 'Not ready'} hint={evalStatus?.invalid_line_count ? `${evalStatus.invalid_line_count} invalid rows` : 'No scores until evaluation runs'} tone="amber"/></div>
    <div className="content-grid overview-grid"><section className="panel"><PanelTitle eyebrow="WORKFLOW" title="From question to evidence" description="Inspect each step instead of trusting a black-box answer."/><div className="workflow-list"><WorkflowStep number="01" title="Ask a question" text="Query your permitted document collection." icon={MessageSquareText}/><WorkflowStep number="02" title="Verify atomic claims" text="Review each claim's status and cited passage." icon={ShieldCheck}/><WorkflowStep number="03" title="Evaluate on labels" text="Compare predictions against reviewed ground truth." icon={Target}/></div><button className="button secondary full" onClick={() => onNavigate('ask')}>Start a verification <ArrowRight size={16}/></button></section><section className="panel"><PanelTitle eyebrow="CLASSIFICATION SCHEMA" title="Four claim outcomes" description="Every factual claim is assigned one of these labels."/><div className="label-list">{LABELS.map((label, i) => <div className="label-row" key={label.key}><div className={`label-symbol ${label.tone}`}>{i === 0 ? <CheckCircle2 size={18}/> : i === 1 ? <XCircle size={18}/> : i === 2 ? <SlidersHorizontal size={18}/> : <CircleHelp size={18}/>}</div><div className="label-copy"><strong>{label.title}</strong><span>{label.detail}</span></div><ArrowDownRight size={16} className="muted-icon"/></div>)}</div></section></div>
    <div className="research-banner"><div className="research-banner-icon"><FlaskConical size={21}/></div><div><strong>Build evidence, not just a demo.</strong><p>Evaluation scores are intentionally blank until a valid labelled dataset has been run.</p></div><button className="button secondary" onClick={() => onNavigate('evaluation')}>Go to evaluation <ArrowRight size={15}/></button></div>
  </>
}
function WorkflowStep({ number, title, text, icon: Icon }) { return <div className="workflow-step"><div className="step-number">{number}</div><div className="step-icon"><Icon size={18}/></div><div className="step-copy"><strong>{title}</strong><p>{text}</p></div></div> }

function AskPage({ question, setQuestion, topK, setTopK, loading, result, counts, onSubmit }) {
  const evidenceFor = ids => (ids || []).map(id => ({ id, item: result?.evidence?.[id - 1] })).filter(x => x.item)
  return <>
    <PanelTitle eyebrow="ASK & VERIFY" title="Question the documents" description="Answers are generated from retrieved passages and then checked claim by claim."/>
    <div className="ask-layout"><section className="panel ask-form-panel"><form onSubmit={onSubmit}><label className="field-label" htmlFor="question">Your question</label><textarea id="question" value={question} onChange={e => setQuestion(e.target.value)} placeholder="e.g. What responsibilities does top management have under Clause 5.1?" rows={4} maxLength={2000}/><div className="form-bottom"><label className="inline-field">Evidence passages <select value={topK} onChange={e => setTopK(Number(e.target.value))}>{[3,5,8,10,15,20].map(n => <option key={n} value={n}>{n} passages</option>)}</select></label><span className="char-count">{question.length}/2000</span></div><button className="button primary full" type="submit" disabled={loading || !question.trim()}>{loading ? <><LoaderCircle className="spin" size={17}/> Verifying claims…</> : <><ShieldCheck size={17}/> Generate & verify <ArrowRight size={16}/></>}</button><p className="form-note"><AlertCircle size={14}/> Responses may take time because claim verification calls the LLM. Do not treat similarity scores as confidence.</p></form></section><section className="panel ask-side-panel"><div className="side-panel-heading"><div className="side-icon"><BookOpen size={18}/></div><div><strong>What you'll get</strong><span>Traceable answer output</span></div></div><ul className="feature-list"><li><CheckCircle2 size={16}/> Answer-level status and abstention reason</li><li><CheckCircle2 size={16}/> Atomic claims with four-class labels</li><li><CheckCircle2 size={16}/> Evidence source, page and passage text</li><li><CheckCircle2 size={16}/> Limitations and evidence gaps</li></ul><div className="side-tip"><strong>Good evaluation practice</strong><p>Use a question with a clear answer in your indexed PDFs, then compare with an unanswerable question to inspect abstention.</p></div></section></div>
    {result && <div className="result-area"><div className="result-header"><div><div className="eyebrow">VERIFICATION RESULT</div><h2>Answer analysis</h2><p>Review the overall decision and then inspect each individual claim.</p></div><Badge status={result.status}>{human(result.status)}</Badge></div><section className="panel answer-panel"><div className="answer-panel-top"><div className="answer-label"><Sparkles size={16}/> GENERATED ANSWER</div><span className={`abstain-tag ${result.abstained ? 'yes' : 'no'}`}>{result.abstained ? 'Abstained' : 'Did not abstain'}</span></div>{result.answer ? <p className="answer-text">{result.answer}</p> : <div className="empty-answer"><CircleHelp size={18}/><span>No answer was returned. The system abstained rather than provide an unverified answer.</span></div>}{result.abstention_reason && <div className="reason-box"><strong>Abstention reason</strong><p>{result.abstention_reason}</p></div>}{result.limitations?.length > 0 && <div className="limitations"><strong>Limitations</strong><ul>{result.limitations.map((item,i)=><li key={i}>{item}</li>)}</ul></div>}</section>
      <div className="section-heading compact"><div><div className="eyebrow">CLAIM-LEVEL RESULTS</div><h2>Claim breakdown <span className="count-pill">{result.claims?.length || 0}</span></h2></div></div>
      {result.claims?.length ? <div className="claim-list">{result.claims.map(claim => <article className="panel claim-card" key={claim.claim_id}><div className="claim-head"><span className="claim-id">CLAIM {String(claim.claim_id).padStart(2,'0')}</span><Badge status={claim.status}/></div><p className="claim-text">{claim.text}</p>{claim.explanation && <p className="claim-explanation">{claim.explanation}</p>}<div className="claim-evidence">{evidenceFor(claim.evidence_ids).length ? <><div className="evidence-title"><BookOpen size={15}/> Cited evidence</div>{evidenceFor(claim.evidence_ids).map(({id,item})=><div className="citation-card" key={id}><div className="citation-meta"><span>[E{id}] {item.source} · Page {item.page}</span>{item.similarity != null && <span>Similarity {item.similarity.toFixed(3)}</span>}</div><p>{item.text}</p></div>)}</> : <div className="no-citation"><AlertCircle size={15}/> No evidence IDs were returned for this claim.</div>}</div></article>)}</div> : <div className="metrics-grid mini-metrics">{LABELS.map(label=><MetricCard key={label.key} icon={label.key==='supported'?CheckCircle2:label.key==='contradicted'?XCircle:label.key==='partially_supported'?SlidersHorizontal:CircleHelp} label={label.title} value={counts[label.key]} hint="Claims in this category" tone={label.tone}/>)}</div>}
      {result.evidence?.length > 0 && <section className="panel retrieved-panel"><PanelTitle eyebrow="RETRIEVAL TRACE" title="All retrieved passages" description="These are retrieval results, not automatically proof of a claim."/><div className="retrieved-list">{result.evidence.map((item,i)=><details className="retrieved-item" key={`${item.source}-${item.chunk_id}-${i}`}><summary><span className="evidence-index">E{i+1}</span><span className="retrieved-source"><strong>{item.source}</strong><small>Page {item.page} · Chunk {item.chunk_id}</small></span><span className="similarity-pill">{item.similarity == null ? 'N/A' : item.similarity.toFixed(3)}</span><ChevronDown size={16}/></summary><p>{item.text}</p></details>)}</div></section>}
    </div>}
  </>
}

function EvaluationPage({ status, report, loading, onRun, onRefresh }) {
  const classification = report?.classification
  const abstention = report?.abstention
  const citations = report?.citations
  return <>
    <PanelTitle eyebrow="RESEARCH EVALUATION" title="Evaluation lab" description="Run the verifier against manually labelled claim/evidence examples. Metrics remain blank until a run completes." action={<button className="button subtle" onClick={onRefresh}><RefreshCw size={15}/> Refresh dataset</button>}/>
    <div className="eval-status-card"><div className={`dataset-mark ${status?.ready ? 'ready' : ''}`}><Database size={22}/></div><div className="dataset-copy"><strong>{status?.example_count ? `${status.example_count} labelled examples available` : 'No labelled dataset loaded'}</strong><p>{status?.exists ? 'data/evaluation_dataset.jsonl' : 'Create data/evaluation_dataset.jsonl using the documented schema.'}{status?.invalid_line_count > 0 && ` · ${status.invalid_line_count} invalid rows`}</p>{status?.label_counts && <div className="label-chips">{LABELS.map(label=><span key={label.key}>{label.title}: <b>{status.label_counts[label.key] || 0}</b></span>)}</div>}</div><div className="eval-status-actions"><span className={`status-pill ${status?.ready ? 'ready' : 'pending'}`}><span className="mini-dot"/>{status?.ready ? 'Ready to run' : 'Awaiting labels'}</span><button className="button primary" disabled={loading || !status?.ready} onClick={onRun}>{loading ? <><LoaderCircle className="spin" size={16}/> Running…</> : <><FlaskConical size={16}/> Run evaluation</>}</button></div></div>
    {!report && <div className="metrics-grid four-metrics"><MetricCard icon={Target} label="Accuracy" value="—" hint="Not measured yet" tone="blue"/><MetricCard icon={ClipboardCheck} label="Macro precision" value="—" hint="Not measured yet" tone="purple"/><MetricCard icon={Search} label="Macro recall" value="—" hint="Not measured yet" tone="green"/><MetricCard icon={Activity} label="Macro F1-score" value="—" hint="Not measured yet" tone="amber"/></div>}
    {report && <><div className="report-meta"><div><div className="eyebrow">LATEST RUN</div><strong>{report.evaluated_count} examples evaluated</strong><span>{report.error_count} failed examples · {report.dataset_size} total in dataset</span></div><span className="report-tag"><CheckCircle2 size={14}/> Run completed</span></div><div className="metrics-grid four-metrics"><MetricCard icon={Target} label="Accuracy" value={pct(classification?.accuracy)} hint={`${classification?.sample_count ?? 0} classified claims`} tone="blue"/><MetricCard icon={ClipboardCheck} label="Macro precision" value={pct(classification?.macro_precision)} hint="Unweighted class average" tone="purple"/><MetricCard icon={Search} label="Macro recall" value={pct(classification?.macro_recall)} hint="Unweighted class average" tone="green"/><MetricCard icon={Activity} label="Macro F1-score" value={pct(classification?.macro_f1)} hint="Unweighted class average" tone="amber"/></div><div className="content-grid eval-detail-grid"><section className="panel"><PanelTitle eyebrow="FOUR-CLASS RESULTS" title="Per-class metrics" description="Each row is compared with the dataset's expected_status label."/><div className="table-wrap"><table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead><tbody>{LABELS.map(label=>{const row=classification?.per_class?.[label.key];return <tr key={label.key}><td><Badge status={label.key}/></td><td>{pct(row?.precision)}</td><td>{pct(row?.recall)}</td><td>{pct(row?.f1)}</td><td>{row?.support ?? 0}</td></tr>})}</tbody></table></div></section><section className="panel"><PanelTitle eyebrow="SAFE ANSWERING" title="Abstention quality" description="A prediction is counted as abstention when the verifier returns insufficient evidence."/><div className="abstain-metrics">{[['Accuracy',abstention?.accuracy],['Precision',abstention?.precision],['Recall',abstention?.recall],['F1-score',abstention?.f1]].map(([label,value])=><div key={label}><span>{label}</span><strong>{pct(value)}</strong></div>)}</div><div className="metric-footnote">{abstention?.sample_count ?? 0} examples · true positives: {abstention?.true_positive ?? '—'} · false positives: {abstention?.false_positive ?? '—'}</div></section></div><section className="panel citation-panel"><PanelTitle eyebrow="SOURCE TRACEABILITY" title="Citation quality" description="Compares predicted evidence IDs against manually labelled expected_evidence_ids."/><div className="citation-metric-grid">{[['Citation precision',citations?.precision],['Citation recall',citations?.recall],['Citation F1',citations?.f1]].map(([label,value])=><div className="citation-metric" key={label}><span>{label}</span><strong>{pct(value)}</strong></div>)}</div><p className="metric-footnote">{citations?.evaluated_examples ?? 0} examples with at least one expected or predicted citation were scored. Citation IDs refer to 1-based positions in each example's evidence list.</p></section><section className="panel results-panel"><PanelTitle eyebrow="ERROR ANALYSIS" title="Example-by-example results" description="Use incorrect predictions to improve prompts, retrieval, and annotation guidelines."/><ResultsTable results={report.results || []}/>{report.errors?.length > 0 && <div className="error-rows"><strong>Examples that failed to evaluate</strong>{report.errors.map((item,i)=><p key={i}>{item.id}: {item.error}</p>)}</div>}</section><section className="panel methodology"><div className="method-icon"><AlertCircle size={19}/></div><div><strong>Interpretation note</strong><p>{report.notes?.join(' ')}</p><p>These scores describe the labelled examples and configuration used in this run. They are not a guarantee of performance on other domains or documents.</p></div></section></>}
    <section className="panel dataset-instructions"><div className="instructions-icon"><UploadCloud size={20}/></div><div><strong>Dataset format and annotation rules</strong><p>Each JSONL row needs a unique id, domain, question, atomic claim, expected_status, expected_abstain, a list of evidence passages, and expected_evidence_ids. Use independently reviewed labels; do not label examples based on the model's prediction.</p><a href="/evaluation-dataset-schema.json" target="_blank" rel="noreferrer">View dataset schema <ArrowRight size={14}/></a></div></section>
  </>
}
function ResultsTable({ results }) { if (!results.length) return <Empty icon={ClipboardCheck} title="No rows to display" text="Results will appear here after a successful evaluation run."/>; return <div className="table-wrap results-table-wrap"><table><thead><tr><th>ID / Domain</th><th>Expected</th><th>Predicted</th><th>Abstention</th><th>Citations</th></tr></thead><tbody>{results.map(row=><tr key={row.id}><td><strong>{row.id}</strong><small className="cell-sub">{row.domain}</small></td><td><Badge status={row.expected_status}/></td><td><Badge status={row.predicted_status}/><small className="cell-sub">{row.status_correct ? 'Correct label' : 'Mismatch'}</small></td><td><span className={`result-check ${row.abstention_correct ? 'good' : 'bad'}`}>{row.abstention_correct ? 'Correct' : 'Mismatch'}</span><small className="cell-sub">Expected: {row.expected_abstain ? 'abstain' : 'answer'}</small></td><td><span className={`result-check ${row.citation_correct ? 'good' : 'bad'}`}>{row.citation_correct ? 'Exact match' : 'Mismatch'}</span><small className="cell-sub">Predicted {row.predicted_evidence_ids.length} / expected {row.expected_evidence_ids.length}</small></td></tr>)}</tbody></table></div> }

function DocumentsPage({ documents, loading, onReindex, onRefresh }) {
  return <><PanelTitle eyebrow="KNOWLEDGE BASE" title="Document collection" description="Index permitted PDF sources across domains. The backend rebuilds embeddings when you reindex." action={<button className="button subtle" onClick={onRefresh}><RefreshCw size={15}/> Refresh</button>}/><div className="doc-stats metrics-grid"><MetricCard icon={FileText} label="PDF sources indexed" value={documents?.document_count ?? '—'} hint="Unique source files" tone="blue"/><MetricCard icon={BookOpen} label="Pages indexed" value={documents?.documents?.reduce((sum,d)=>sum+d.page_count,0) ?? '—'} hint="Extractable-text pages" tone="purple"/><MetricCard icon={Layers3} label="Evidence chunks" value={documents?.chunk_count ?? '—'} hint="Used by FAISS retrieval" tone="green"/><MetricCard icon={Activity} label="Index status" value={documents?.index_ready ? 'Ready' : 'Offline'} hint="Loaded in backend memory" tone={documents?.index_ready ? 'green' : 'red'}/></div><section className="panel doc-panel"><PanelTitle eyebrow="INDEXED SOURCES" title="Available PDFs" description="Source and page metadata are preserved for citation display." action={<button className="button primary" onClick={onReindex} disabled={loading}>{loading ? <><LoaderCircle className="spin" size={16}/> Rebuilding…</> : <><RefreshCw size={16}/> Rebuild index</>}</button>}/>{documents?.documents?.length ? <div className="document-list">{documents.documents.map(doc=><div className="document-row" key={doc.source}><div className="file-type-icon"><FileText size={20}/></div><div className="document-copy"><strong>{doc.source}</strong><span>PDF document · indexed evidence source</span></div><div className="document-numbers"><strong>{doc.page_count}</strong><span>pages</span></div><div className="document-numbers"><strong>{doc.chunk_count}</strong><span>chunks</span></div><span className="status-pill ready"><span className="mini-dot"/> Indexed</span></div>)}</div> : <Empty icon={FileText} title="No indexed documents" text="Start the backend with at least one readable PDF in data/documents/."/>}</section><section className="panel add-doc-panel"><div className="add-doc-icon"><UploadCloud size={21}/></div><div><strong>Add more permitted documents</strong><p>Place additional PDF files inside <code>data/documents/</code> in your project. Choose documents from different domains only when you have permission to use them. Then select <b>Rebuild index</b>. The server currently ingests PDFs; scanned/image-only PDFs need OCR before they can be indexed.</p><button className="button secondary" onClick={onReindex} disabled={loading}><RefreshCw size={15}/> Reindex collection</button></div></section></>
}
