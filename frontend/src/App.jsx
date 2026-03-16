import { useState, useRef, useEffect } from 'react';
import {
  Upload, CheckCircle, AlertCircle, X, Briefcase,
  Sparkles, ChevronRight, Star, Lightbulb, Target,
  TrendingUp, Zap, Brain, Eye, Columns2,
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─── Animated Circular Score Ring ────────────────────────────────────────────
function ScoreRing({ score, label }) {
  const [displayScore, setDisplayScore] = useState(0);
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (displayScore / 100) * circumference;

  useEffect(() => {
    let start = 0;
    const end = score;
    const duration = 1200;
    const step = (end / duration) * 16;
    const timer = setInterval(() => {
      start += step;
      if (start >= end) { setDisplayScore(end); clearInterval(timer); }
      else setDisplayScore(Math.round(start));
    }, 16);
    return () => clearInterval(timer);
  }, [score]);

  const ringColor =
    score >= 80 ? '#22c55e' :
    score >= 60 ? '#3b82f6' :
    score >= 40 ? '#f59e0b' : '#ef4444';

  const labelBg =
    score >= 80 ? 'bg-green-500/20 text-green-300 border-green-500/30' :
    score >= 60 ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' :
    score >= 40 ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
    'bg-red-500/20 text-red-300 border-red-500/30';

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-44 h-44">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 180 180">
          <circle cx="90" cy="90" r={radius} fill="none"
            stroke="rgba(255,255,255,0.07)" strokeWidth="12" />
          <circle cx="90" cy="90" r={radius} fill="none"
            stroke={ringColor} strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 0.05s linear', filter: `drop-shadow(0 0 10px ${ringColor})` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-black text-white">{displayScore}%</span>
          <span className="text-xs text-white/50 uppercase tracking-widest mt-1">match</span>
        </div>
      </div>
      <span className={`mt-3 px-4 py-1 rounded-full text-sm font-semibold border ${labelBg}`}>
        {label}
      </span>
    </div>
  );
}

// ─── Category Bar ─────────────────────────────────────────────────────────────
function CategoryBar({ label, value }) {
  const [width, setWidth] = useState(0);
  useEffect(() => { const t = setTimeout(() => setWidth(value), 100); return () => clearTimeout(t); }, [value]);
  const color = value >= 75 ? '#22c55e' : value >= 50 ? '#3b82f6' : value >= 25 ? '#f59e0b' : '#ef4444';

  return (
    <div className="mb-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm text-white/70 capitalize">{label.replace('_', ' ')}</span>
        <span className="text-sm font-bold" style={{ color }}>{value}%</span>
      </div>
      <div className="h-2 rounded-full bg-white/10 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${width}%`, backgroundColor: color, boxShadow: `0 0 8px ${color}40` }} />
      </div>
    </div>
  );
}

// ─── Skill Tag ────────────────────────────────────────────────────────────────
function SkillTag({ skill, type }) {
  const styles = {
    matched: 'bg-green-500/15 text-green-300 border-green-500/30',
    preferred: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
    missing: 'bg-red-500/15 text-red-300 border-red-500/30',
  };
  const titles = {
    matched: 'Matched required skill',
    preferred: 'Matched preferred skill',
    missing: 'Missing skill',
  };
  return (
    <span
      title={titles[type]}
      className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors hover:border-white/30 cursor-default ${styles[type]}`}
    >
      {skill}
    </span>
  );
}

// ─── Glass Card ───────────────────────────────────────────────────────────────
function GlassCard({ children, className = '', accentColor = '' }) {
  return (
    <div
      className={`rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md p-6 hover:border-white/20 transition-colors duration-200 ${className}`}
      style={accentColor ? { borderTopColor: accentColor, borderTopWidth: '2px' } : {}}
    >
      {children}
    </div>
  );
}

// ─── Section Header ───────────────────────────────────────────────────────────
function SectionHeader({ icon: Icon, title, color = 'text-white' }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon className={`w-5 h-5 ${color}`} />
      <h3 className={`font-bold text-base ${color}`}>{title}</h3>
    </div>
  );
}

// ─── Loading Skeleton ─────────────────────────────────────────────────────────
function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-48 rounded-2xl bg-white/5" />
      <div className="grid md:grid-cols-2 gap-4">
        <div className="h-40 rounded-2xl bg-white/5" />
        <div className="h-40 rounded-2xl bg-white/5" />
      </div>
      <div className="h-32 rounded-2xl bg-white/5" />
    </div>
  );
}

// ─── Modal ────────────────────────────────────────────────────────────────────
function Modal({ onClose, title, children, size = 'md' }) {
  const sizeClass = {
    md: 'w-full max-w-2xl',
    lg: 'w-[90vw] max-w-5xl h-[85vh]',
    xl: 'w-[95vw] max-w-none h-[90vh]',
  }[size];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className={`relative flex flex-col ${sizeClass} rounded-2xl border border-white/15 bg-[#0e0e1a] shadow-2xl`}
        style={{ animation: 'slideUp 0.2s ease-out' }}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10 flex-shrink-0">
          <h2 className="text-sm font-bold text-white/80 truncate pr-4">{title}</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 transition-colors flex-shrink-0"
          >
            <X className="w-4 h-4 text-white/50" />
          </button>
        </div>
        {/* Modal Body */}
        <div className="flex-1 overflow-hidden min-h-0">
          {children}
        </div>
      </div>
    </div>
  );
}

// ─── Annotated Job Description ────────────────────────────────────────────────
function AnnotatedJobDescription({ text, matchedSkills = [], preferredSkills = [], missingSkills = [] }) {
  const hasAnnotations = matchedSkills.length > 0 || preferredSkills.length > 0 || missingSkills.length > 0;

  if (!hasAnnotations) {
    return (
      <pre className="whitespace-pre-wrap text-white/70 text-sm leading-relaxed font-sans">
        {text}
      </pre>
    );
  }

  // Build skill → type map (longest skill first to avoid partial overlaps)
  const allSkills = [
    ...matchedSkills.map(s => ({ s, type: 'matched' })),
    ...preferredSkills.map(s => ({ s, type: 'preferred' })),
    ...missingSkills.map(s => ({ s, type: 'missing' })),
  ].sort((a, b) => b.s.length - a.s.length);

  const skillMap = {};
  allSkills.forEach(({ s, type }) => { skillMap[s.toLowerCase()] = type; });

  const pattern = allSkills
    .map(({ s }) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|');
  const regex = new RegExp(`(${pattern})`, 'gi');
  const parts = text.split(regex);

  const markStyles = {
    matched: 'bg-green-500/25 text-green-200 rounded px-0.5',
    preferred: 'bg-blue-500/25 text-blue-200 rounded px-0.5',
    missing: 'bg-red-500/25 text-red-200 rounded px-0.5',
  };

  return (
    <pre className="whitespace-pre-wrap text-white/70 text-sm leading-relaxed font-sans">
      {parts.map((part, i) => {
        const type = skillMap[part.toLowerCase()];
        if (type) {
          return (
            <mark key={i} className={`${markStyles[type]} not-italic`} title={`${type} skill`}>
              {part}
            </mark>
          );
        }
        return part;
      })}
    </pre>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isRateLimitError, setIsRateLimitError] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [resumeObjectUrl, setResumeObjectUrl] = useState(null);
  const [showResumeModal, setShowResumeModal] = useState(false);
  const [showJobModal, setShowJobModal] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);
  // Compare mobile tab state
  const [compareTab, setCompareTab] = useState('resume');

  const fileInputRef = useRef(null);
  const resultsRef = useRef(null);

  // Create / revoke PDF object URL when file changes
  useEffect(() => {
    if (file) {
      const url = URL.createObjectURL(file);
      setResumeObjectUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setResumeObjectUrl(null);
    }
  }, [file]);

  // ESC closes any open modal
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') {
        setShowResumeModal(false);
        setShowJobModal(false);
        setShowCompareModal(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const handleDrag = (e) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]);
  };

  const handleFile = (f) => {
    if (f.type === 'application/pdf') { setFile(f); setError(null); }
    else setError('Please upload a PDF file.');
  };

  const clearFile = () => {
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async () => {
    if (!file || !jobDescription.trim()) {
      setError('Please provide both a resume and a job description.');
      return;
    }
    setIsLoading(true); setError(null); setIsRateLimitError(false); setResult(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_description', jobDescription);
    try {
      const res = await fetch(`${API_URL}/api/calculate-match`, { method: 'POST', body: formData });
      if (!res.ok) {
        const d = await res.json();
        if (res.status === 429) setIsRateLimitError(true);
        throw new Error(d.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) {
      setError(err.message || 'Failed to connect. Is the backend running on port 8000?');
    } finally {
      setIsLoading(false);
    }
  };

  const hasCategoryScores = result?.category_scores && Object.keys(result.category_scores).length > 0;
  const canCompare = !!file && !!jobDescription.trim();

  const scoreAccentColor =
    result?.score >= 80 ? '#22c55e' :
    result?.score >= 60 ? '#3b82f6' :
    result?.score >= 40 ? '#f59e0b' :
    result?.score != null ? '#ef4444' : '';

  return (
    <div className="min-h-screen bg-[#0a0a12] text-white font-sans">
      {/* Background glows */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] bg-indigo-700/20 rounded-full blur-[120px]" />
        <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] bg-purple-700/15 rounded-full blur-[120px]" />
        {/* Subtle dot grid */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
            backgroundSize: '28px 28px',
          }}
        />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-4 py-10">

        {/* ── Header ── */}
        <header className="text-center mb-10 pb-8 border-b border-white/5">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-900/50">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r from-white via-white/90 to-white/50 bg-clip-text text-transparent">
              Smart Resume Matcher
            </h1>
          </div>
          <p className="text-white/35 text-sm tracking-wide">
            AI-powered analysis · Semantic skill matching · Groq narrative insights
          </p>
        </header>

        {/* ── Input Panel ── */}
        <div className="grid lg:grid-cols-2 gap-4 mb-4">

          {/* Resume Upload */}
          <GlassCard>
            <p className="text-xs font-semibold text-white/50 uppercase tracking-widest mb-3">Resume (PDF)</p>
            {file ? (
              <div className="flex items-center justify-between p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
                <div className="flex items-center gap-3 min-w-0">
                  <CheckCircle className="w-5 h-5 text-indigo-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white truncate max-w-[150px]">{file.name}</p>
                    <p className="text-xs text-white/40">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => setShowResumeModal(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/35 text-indigo-300 text-xs font-medium transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" /> View
                  </button>
                  <button onClick={clearFile} className="p-1.5 rounded-lg hover:bg-white/10 transition-colors">
                    <X className="w-4 h-4 text-white/50" />
                  </button>
                </div>
              </div>
            ) : (
              <div
                onDragEnter={handleDrag} onDragLeave={handleDrag}
                onDragOver={handleDrag} onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                  dragActive ? 'border-indigo-400 bg-indigo-500/10' : 'border-white/10 hover:border-indigo-500/50 hover:bg-white/5'
                }`}
              >
                <Upload className="w-10 h-10 text-white/20 mx-auto mb-3" />
                <p className="text-white/50 text-sm">Drag & drop your PDF here</p>
                <p className="text-white/25 text-xs mt-1">or click to browse</p>
                <input ref={fileInputRef} type="file" accept=".pdf" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} className="hidden" />
              </div>
            )}
          </GlassCard>

          {/* Job Description */}
          <GlassCard>
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold text-white/50 uppercase tracking-widest">Job Description</p>
              {jobDescription.trim() && (
                <button
                  onClick={() => setShowJobModal(true)}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/70 text-xs font-medium transition-colors"
                >
                  <Eye className="w-3 h-3" /> View
                </button>
              )}
            </div>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the full job description here…"
              className="w-full h-[148px] bg-transparent text-white/80 placeholder-white/20 text-sm resize-none outline-none leading-relaxed"
            />
            {jobDescription.length > 0 && (
              <p className="text-right text-white/20 text-xs mt-1">{jobDescription.length} chars</p>
            )}
          </GlassCard>
        </div>

        {/* ── Action Buttons ── */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-8">
          {/* Compare Button */}
          <button
            onClick={() => { setCompareTab('resume'); setShowCompareModal(true); }}
            disabled={!canCompare}
            className="flex items-center gap-2 px-6 py-3.5 rounded-2xl font-semibold text-sm text-white/70 border border-white/15 bg-white/5 hover:bg-white/10 hover:border-white/25 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200"
          >
            <Columns2 className="w-4 h-4" />
            Compare
          </button>

          {/* Analyse Button */}
          <button
            onClick={handleSubmit}
            disabled={!file || !jobDescription.trim() || isLoading}
            className="relative group px-10 py-3.5 rounded-2xl font-bold text-white bg-gradient-to-r from-indigo-600 to-purple-600 shadow-lg shadow-indigo-900/50 hover:shadow-indigo-700/50 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300 hover:scale-105 disabled:hover:scale-100"
          >
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-400 to-purple-400 opacity-0 group-hover:opacity-20 transition-opacity" />
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Analysing…
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Analyse Match
              </span>
            )}
          </button>
        </div>

        {/* ── Error ── */}
        {error && (
          <div className={`mb-6 p-4 rounded-xl flex items-start gap-3 ${
            isRateLimitError
              ? 'bg-amber-500/10 border border-amber-500/30'
              : 'bg-red-500/10 border border-red-500/30'
          }`}>
            <AlertCircle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${isRateLimitError ? 'text-amber-400' : 'text-red-400'}`} />
            <div>
              <p className={`text-sm font-medium ${isRateLimitError ? 'text-amber-300' : 'text-red-300'}`}>{error}</p>
              {isRateLimitError && (
                <p className="text-amber-400/70 text-xs mt-1">Wait ~60 seconds, then try again.</p>
              )}
            </div>
          </div>
        )}

        {/* ── Loading Skeleton ── */}
        {isLoading && <LoadingSkeleton />}

        {/* ── Results ── */}
        {result && !isLoading && (
          <div ref={resultsRef} className="space-y-4 animate-fadeIn">

            {/* Score Hero */}
            <GlassCard
              className="flex flex-col sm:flex-row items-center gap-8"
              accentColor={scoreAccentColor}
            >
              <ScoreRing score={result.score} label={result.score_label} />

              <div className="flex-1 space-y-4 text-center sm:text-left">
                {result.experience_level && (
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-500/30">
                    <Briefcase className="w-3.5 h-3.5 text-purple-300" />
                    <span className="text-xs text-purple-200">{result.experience_level} role</span>
                  </div>
                )}

                {/* Breakdown pills */}
                <div className="flex flex-wrap gap-3 justify-center sm:justify-start">
                  <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10">
                    <p className="text-xs text-white/40 mb-0.5">Required Skills</p>
                    <p className="text-lg font-bold text-white">{result.breakdown?.required_match}</p>
                  </div>
                  <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10">
                    <p className="text-xs text-white/40 mb-0.5">Preferred Skills</p>
                    <p className="text-lg font-bold text-white">{result.breakdown?.preferred_match}</p>
                  </div>
                  {result.semantic_similarity != null && (
                    <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10">
                      <p className="text-xs text-white/40 mb-0.5">Semantic Fit</p>
                      <p className="text-lg font-bold text-indigo-300">{result.semantic_similarity}%</p>
                    </div>
                  )}
                </div>

                {/* Insights */}
                {result.suggestions?.length > 0 && (
                  <ul className="space-y-1">
                    {result.suggestions.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-white/60">
                        <ChevronRight className="w-4 h-4 flex-shrink-0 mt-0.5 text-indigo-400" />
                        {s}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </GlassCard>

            {/* AI Summary */}
            {result.ai_analysis?.summary && (
              <GlassCard>
                <SectionHeader icon={Brain} title="AI Summary" color="text-indigo-300" />
                <p className="text-white/70 text-sm leading-relaxed">{result.ai_analysis.summary}</p>
              </GlassCard>
            )}

            {/* Category Scores */}
            {hasCategoryScores && (
              <GlassCard>
                <SectionHeader icon={TrendingUp} title="Skill Category Breakdown" color="text-blue-300" />
                <div className="grid sm:grid-cols-2 gap-x-8">
                  {Object.entries(result.category_scores).map(([cat, val]) => (
                    <CategoryBar key={cat} label={cat} value={val} />
                  ))}
                </div>
              </GlassCard>
            )}

            {/* Skills Grid */}
            <div className="grid md:grid-cols-3 gap-4">
              {result.matched_skills?.length > 0 && (
                <GlassCard>
                  <SectionHeader icon={CheckCircle} title="Matched Skills" color="text-green-400" />
                  <div className="flex flex-wrap gap-2">
                    {result.matched_skills.map((s, i) => <SkillTag key={i} skill={s} type="matched" />)}
                  </div>
                </GlassCard>
              )}
              {result.matched_preferred?.length > 0 && (
                <GlassCard>
                  <SectionHeader icon={Star} title="Bonus Skills" color="text-blue-400" />
                  <div className="flex flex-wrap gap-2">
                    {result.matched_preferred.map((s, i) => <SkillTag key={i} skill={s} type="preferred" />)}
                  </div>
                </GlassCard>
              )}
              {result.missing_critical?.length > 0 && (
                <GlassCard>
                  <SectionHeader icon={AlertCircle} title="Missing Skills" color="text-red-400" />
                  <div className="flex flex-wrap gap-2">
                    {result.missing_critical.map((s, i) => <SkillTag key={i} skill={s} type="missing" />)}
                  </div>
                </GlassCard>
              )}
            </div>

            {/* Matched Areas */}
            {result.ai_analysis?.matched_areas?.length > 0 && (
              <GlassCard>
                <SectionHeader icon={Target} title="Strong Areas" color="text-green-300" />
                <ul className="space-y-2">
                  {result.ai_analysis.matched_areas.map((area, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-white/70">
                      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-green-500/20 text-green-300 flex items-center justify-center text-xs font-bold">{i + 1}</span>
                      {area}
                    </li>
                  ))}
                </ul>
              </GlassCard>
            )}

            {/* Career Tips */}
            {result.ai_analysis?.career_tips?.length > 0 && (
              <GlassCard>
                <SectionHeader icon={Lightbulb} title="Career Tips" color="text-amber-300" />
                <ul className="space-y-3">
                  {result.ai_analysis.career_tips.map((tip, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-white/70">
                      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-amber-500/20 text-amber-300 flex items-center justify-center text-xs font-bold">{i + 1}</span>
                      {tip}
                    </li>
                  ))}
                </ul>
              </GlassCard>
            )}

          </div>
        )}

        {/* ── Empty State ── */}
        {!result && !isLoading && !error && (
          <div className="text-center py-20 rounded-2xl border border-white/5 bg-white/[0.02]">
            <div className="relative w-16 h-16 mx-auto mb-5">
              <div className="absolute inset-0 rounded-full border-2 border-white/10 animate-ping" style={{ animationDuration: '2.5s' }} />
              <div className="absolute inset-0 flex items-center justify-center">
                <Briefcase className="w-8 h-8 text-white/15" />
              </div>
            </div>
            <p className="text-white/25 text-sm">Upload your resume and paste a job description to get started</p>
            <p className="text-white/12 text-xs mt-2">PDF format · Any job description text</p>
          </div>
        )}

        <p className="text-center text-white/15 text-xs mt-10">
          Powered by skillNer · sentence-transformers · Groq AI
        </p>
      </div>

      {/* ══════════════════════════ MODALS ══════════════════════════ */}

      {/* Resume PDF Modal */}
      {showResumeModal && resumeObjectUrl && (
        <Modal onClose={() => setShowResumeModal(false)} title={file?.name} size="lg">
          <iframe
            src={resumeObjectUrl}
            className="w-full h-full rounded-b-2xl"
            title="Resume Preview"
          />
        </Modal>
      )}

      {/* Job Description Modal */}
      {showJobModal && (
        <Modal onClose={() => setShowJobModal(false)} title="Job Description" size="md">
          <div className="h-full overflow-y-auto p-5">
            {result && (
              <div className="flex flex-wrap items-center gap-3 mb-4 pb-4 border-b border-white/10">
                <span className="text-xs text-white/40 font-medium">Skill highlights from last analysis:</span>
                <span className="flex items-center gap-1.5 text-xs text-green-300">
                  <span className="w-2 h-2 rounded-full bg-green-500/60 inline-block" /> Matched
                </span>
                <span className="flex items-center gap-1.5 text-xs text-blue-300">
                  <span className="w-2 h-2 rounded-full bg-blue-500/60 inline-block" /> Preferred
                </span>
                <span className="flex items-center gap-1.5 text-xs text-red-300">
                  <span className="w-2 h-2 rounded-full bg-red-500/60 inline-block" /> Missing
                </span>
              </div>
            )}
            <AnnotatedJobDescription
              text={jobDescription}
              matchedSkills={result?.matched_skills}
              preferredSkills={result?.matched_preferred}
              missingSkills={result?.missing_critical}
            />
          </div>
        </Modal>
      )}

      {/* Compare Modal */}
      {showCompareModal && (
        <Modal onClose={() => setShowCompareModal(false)} title="Resume vs. Job Description" size="xl">
          <div className="flex flex-col h-full">

            {/* Annotation notice if analysis was done */}
            {result && (
              <div className="flex flex-wrap items-center gap-4 px-5 py-2.5 border-b border-white/10 flex-shrink-0">
                <span className="text-xs text-white/35">Showing skill annotations from last analysis</span>
                <div className="flex items-center gap-3 ml-auto">
                  <span className="flex items-center gap-1.5 text-xs text-green-300">
                    <span className="w-2 h-2 rounded-full bg-green-500/60 inline-block" /> Matched
                  </span>
                  <span className="flex items-center gap-1.5 text-xs text-blue-300">
                    <span className="w-2 h-2 rounded-full bg-blue-500/60 inline-block" /> Preferred
                  </span>
                  <span className="flex items-center gap-1.5 text-xs text-red-300">
                    <span className="w-2 h-2 rounded-full bg-red-500/60 inline-block" /> Missing
                  </span>
                </div>
              </div>
            )}

            {/* Mobile tabs */}
            <div className="flex sm:hidden border-b border-white/10 flex-shrink-0">
              <button
                onClick={() => setCompareTab('resume')}
                className={`flex-1 py-2.5 text-xs font-semibold transition-colors ${compareTab === 'resume' ? 'text-indigo-300 border-b-2 border-indigo-400' : 'text-white/40 hover:text-white/60'}`}
              >
                Resume
              </button>
              <button
                onClick={() => setCompareTab('job')}
                className={`flex-1 py-2.5 text-xs font-semibold transition-colors ${compareTab === 'job' ? 'text-indigo-300 border-b-2 border-indigo-400' : 'text-white/40 hover:text-white/60'}`}
              >
                Job Description
              </button>
            </div>

            {/* Split view (desktop) / Single panel (mobile) */}
            <div className="flex-1 flex min-h-0 overflow-hidden">

              {/* Left – PDF */}
              <div className={`${compareTab === 'resume' ? 'flex' : 'hidden'} sm:flex flex-col w-full sm:w-1/2 border-r border-white/10`}>
                <div className="px-4 py-2 text-xs font-semibold text-white/30 uppercase tracking-widest flex-shrink-0 hidden sm:block">
                  Resume
                </div>
                {resumeObjectUrl ? (
                  <iframe
                    src={resumeObjectUrl}
                    className="flex-1 w-full"
                    title="Resume"
                  />
                ) : (
                  <div className="flex-1 flex items-center justify-center text-white/20 text-sm">
                    No PDF loaded
                  </div>
                )}
              </div>

              {/* Right – Annotated JD */}
              <div className={`${compareTab === 'job' ? 'flex' : 'hidden'} sm:flex flex-col w-full sm:w-1/2`}>
                <div className="px-4 py-2 text-xs font-semibold text-white/30 uppercase tracking-widest flex-shrink-0 hidden sm:block">
                  Job Description
                </div>
                <div className="flex-1 overflow-y-auto p-4">
                  <AnnotatedJobDescription
                    text={jobDescription}
                    matchedSkills={result?.matched_skills}
                    preferredSkills={result?.matched_preferred}
                    missingSkills={result?.missing_critical}
                  />
                </div>
              </div>

            </div>
          </div>
        </Modal>
      )}

      {/* Slide-up animation */}
      <style>{`
        @keyframes slideUp {
          from { transform: translateY(12px); opacity: 0; }
          to   { transform: translateY(0);    opacity: 1; }
        }
      `}</style>
    </div>
  );
}
