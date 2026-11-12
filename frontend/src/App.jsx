import React, { useState, useEffect, useRef } from 'react';
import { 
  Dumbbell, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Play, 
  Pause, 
  RotateCcw, 
  FastForward, 
  Layers, 
  ChevronRight, 
  Activity, 
  BookOpen, 
  HelpCircle, 
  Sparkles, 
  Upload, 
  FileVideo, 
  ShieldCheck, 
  ExternalLink,
  Flame,
  ArrowRight
} from 'lucide-react';

export default function App() {
  const [samples, setSamples] = useState([]);
  const [selectedSample, setSelectedSample] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  
  // Job status
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobStage, setJobStage] = useState('');
  const [jobError, setJobError] = useState(null);
  
  // Results
  const [results, setResults] = useState(null);
  const [proMode, setProMode] = useState(false);
  const [activeRepTab, setActiveRepTab] = useState(1);
  const [showStandardsModal, setShowStandardsModal] = useState(false);
  const [standardsData, setStandardsData] = useState(null);

  // Video & Canvas states
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Overlay layer toggles
  const [showSkeleton, setShowSkeleton] = useState(true);
  const [showBarTrail, setShowBarTrail] = useState(true);
  const [showMidfoot, setShowMidfoot] = useState(true);
  const [showDepthPlane, setShowDepthPlane] = useState(true);

  // Fetch samples and standards on mount
  useEffect(() => {
    fetch('/api/samples')
      .then(res => res.json())
      .then(data => setSamples(data))
      .catch(err => console.error("Error loading samples:", err));

    fetch('/api/standards')
      .then(res => res.json())
      .then(data => setStandardsData(data))
      .catch(err => console.error("Error loading standards:", err));
  }, []);

  // Poll job status
  useEffect(() => {
    if (!jobId || jobStatus === 'DONE' || jobStatus === 'FAILED') return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        const data = await res.json();
        setJobStatus(data.status);
        setJobProgress(data.progress || 0);
        setJobStage(data.stage || '');
        
        if (data.status === 'DONE') {
          const resDetail = await fetch(`/api/jobs/${jobId}/results`);
          const resultsData = await resDetail.json();
          setResults(resultsData);
          clearInterval(interval);
        } else if (data.status === 'FAILED') {
          setJobError(data.error || "Analysis failed");
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 750);

    return () => clearInterval(interval);
  }, [jobId, jobStatus]);

  // Synchronize Canvas with Video Playback
  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !results?.overlay_track?.frames) return;

    let animId;
    const ctx = canvas.getContext('2d');
    const frames = results.overlay_track.frames;
    const fps = results.overlay_track.video_metadata.fps || 30.0;

    const render = () => {
      if (video.paused && !video.seeking) {
        animId = requestAnimationFrame(render);
        return;
      }

      const frameIdx = Math.min(frames.length - 1, Math.max(0, Math.floor(video.currentTime * fps)));
      const frameData = frames[frameIdx];

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (frameData) {
        const scaleX = canvas.width / (results.overlay_track.video_metadata.width || 1080);
        const scaleY = canvas.height / (results.overlay_track.video_metadata.height || 1920);

        // 1. Draw Midfoot Axis
        if (showMidfoot && frameData.landmarks?.ankle) {
          const ankle = frameData.landmarks.ankle;
          const facing = results.overlay_track.video_metadata.dominant_facing || 'left';
          const offset = facing === 'right' ? 30 : -30;
          const mx = (ankle.x + offset) * scaleX;
          
          ctx.strokeStyle = 'rgba(16, 185, 129, 0.75)';
          ctx.lineWidth = 2;
          ctx.setLineDash([6, 6]);
          ctx.beginPath();
          ctx.moveTo(mx, canvas.height * 0.15);
          ctx.lineTo(mx, ankle.y * scaleY + 20);
          ctx.stroke();
          ctx.setLineDash([]);
        }

        // 2. Draw Barbell Trail
        if (showBarTrail) {
          ctx.strokeStyle = 'rgba(236, 72, 153, 0.85)';
          ctx.lineWidth = 3;
          ctx.beginPath();
          let started = false;
          const startBack = Math.max(0, frameIdx - 60);
          for (let i = startBack; i <= frameIdx; i++) {
            const f = frames[i];
            if (f?.barbell?.x && f?.barbell?.y && f.barbell.status !== 'LOST') {
              const bx = f.barbell.x * scaleX;
              const by = f.barbell.y * scaleY;
              if (!started) { ctx.moveTo(bx, by); started = true; }
              else { ctx.lineTo(bx, by); }
            }
          }
          if (started) ctx.stroke();

          // Current barbell position
          if (frameData.barbell?.x && frameData.barbell?.status !== 'LOST') {
            const bx = frameData.barbell.x * scaleX;
            const by = frameData.barbell.y * scaleY;
            ctx.fillStyle = '#ec4899';
            ctx.beginPath();
            ctx.arc(bx, by, 7, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.stroke();
          }
        }

        // 3. Draw Skeleton
        if (showSkeleton && frameData.landmarks) {
          const lm = frameData.landmarks;
          const bones = [
            ['shoulder', 'hip', '#38bdf8', 3],
            ['hip', 'knee', '#f59e0b', 3],
            ['knee', 'ankle', '#10b981', 3],
            ['shoulder', 'ear', '#a855f7', 2],
            ['ear', 'eye', '#c084fc', 2]
          ];

          bones.forEach(([p1, p2, color, width]) => {
            if (lm[p1] && lm[p2] && lm[p1].status !== 'LOST' && lm[p2].status !== 'LOST') {
              ctx.strokeStyle = color;
              ctx.lineWidth = width;
              ctx.beginPath();
              ctx.moveTo(lm[p1].x * scaleX, lm[p1].y * scaleY);
              ctx.lineTo(lm[p2].x * scaleX, lm[p2].y * scaleY);
              ctx.stroke();
            }
          });

          // Draw Joint Circles
          Object.entries(lm).forEach(([name, pt]) => {
            if (pt.status !== 'LOST') {
              ctx.fillStyle = pt.status === 'OBSERVED' ? '#10b981' : '#f59e0b';
              ctx.beginPath();
              ctx.arc(pt.x * scaleX, pt.y * scaleY, 5, 0, Math.PI * 2);
              ctx.fill();
              ctx.strokeStyle = '#ffffff';
              ctx.lineWidth = 1.5;
              ctx.stroke();
            }
          });
        }

        // 4. Draw Depth Plane at Bottom
        if (showDepthPlane && (frameData.is_bottom_frame || frameData.phase?.includes('BOTTOM'))) {
          const knee = frameData.landmarks?.knee;
          const hip = frameData.landmarks?.hip;
          if (knee && hip) {
            const ky = knee.y * scaleY;
            const hy = hip.y * scaleY;
            const kx = knee.x * scaleX;

            // Patella plane
            ctx.strokeStyle = '#38bdf8';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(kx - 90, ky);
            ctx.lineTo(kx + 90, ky);
            ctx.stroke();

            // Hip drop indicator
            const isPass = hy > ky;
            ctx.strokeStyle = isPass ? '#10b981' : '#ef4444';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(hip.x * scaleX, hy);
            ctx.lineTo(hip.x * scaleX, ky);
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [results, showSkeleton, showBarTrail, showMidfoot, showDepthPlane]);

  // Handle Video Actions
  const startAnalysis = async (sampleId = null, file = null) => {
    setJobId(null);
    setJobStatus('QUEUED');
    setJobProgress(5);
    setJobStage('Preparing analysis pipeline...');
    setJobError(null);
    setResults(null);

    const formData = new FormData();
    if (sampleId) {
      formData.append('sample_id', sampleId);
    } else if (file) {
      formData.append('file', file);
    }

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setJobId(data.job_id);
      } else {
        setJobError(data.detail || "Failed to start analysis");
        setJobStatus('FAILED');
      }
    } catch (err) {
      setJobError("Network error connecting to API");
      setJobStatus('FAILED');
    }
  };

  const seekToTime = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      setCurrentTime(seconds);
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) videoRef.current.pause();
      else videoRef.current.play();
      setIsPlaying(!isPlaying);
    }
  };

  const changeRate = (rate) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
      setPlaybackRate(rate);
    }
  };

  const stepFrame = (forward = true) => {
    if (videoRef.current) {
      videoRef.current.pause();
      setIsPlaying(false);
      const fps = results?.overlay_track?.video_metadata?.fps || 30.0;
      const step = 1.0 / fps;
      videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime + (forward ? step : -step));
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Dumbbell className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-sky-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                  IRONPATH AI
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  Starting Strength Grounded
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">Consumer & Pro AI Squat Coach</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowStandardsModal(true)}
              className="text-xs font-medium text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900 transition flex items-center gap-1.5"
            >
              <BookOpen className="w-3.5 h-3.5 text-sky-400" />
              <span>Skill Standards</span>
            </button>

            {/* Pro Mode Toggle */}
            <button
              onClick={() => setProMode(!proMode)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition border flex items-center gap-1.5 ${
                proMode 
                  ? 'bg-purple-600 text-white border-purple-500 shadow-md shadow-purple-600/20' 
                  : 'bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>{proMode ? 'Pro Mode Active' : 'Switch to Pro Mode'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 space-y-6">

        {/* Hero Value Prop Banner */}
        <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 p-6 sm:p-8 shadow-xl">
          <div className="relative z-10 max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Personal Coach in Your Pocket</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Instant Squat Form Check & Next-Set Action Fixes
            </h1>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Record from the side at hip height. Our vision AI checks your depth, torso angle, and bar path against 
              <strong className="text-sky-300"> Mark Rippetoe's Starting Strength</strong> standards and tells you exactly what to fix on your next set.
            </p>
          </div>

          {/* Quick 1-Click Try Buttons */}
          <div className="relative z-10 mt-6 pt-6 border-t border-slate-800/80 flex flex-wrap gap-2.5 items-center">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mr-1">Quick 1-Click Try:</span>
            <button
              onClick={() => startAnalysis('common_sample')}
              className="px-3.5 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 text-xs font-bold transition flex items-center gap-2 shadow-lg shadow-sky-500/20 active:scale-95"
            >
              <Dumbbell className="w-4 h-4" />
              <span>Real Lifter Sample (2 Reps)</span>
            </button>
            <button
              onClick={() => startAnalysis('unsuitable_front_view')}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition border border-slate-700 flex items-center gap-2 active:scale-95"
            >
              <XCircle className="w-4 h-4 text-rose-400" />
              <span>Test Front View (Wrong Angle)</span>
            </button>
            <button
              onClick={() => startAnalysis('unsuitable_poor_framing_occlusion')}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition border border-slate-700 flex items-center gap-2 active:scale-95"
            >
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Test Framing Cutoff</span>
            </button>
          </div>
        </section>

        {/* Upload Dropzone */}
        {!results && !jobId && (
          <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 rounded-2xl border-2 border-dashed border-slate-800 hover:border-sky-500/50 bg-slate-900/40 p-8 text-center transition flex flex-col items-center justify-center gap-4 group">
              <div className="w-16 h-16 rounded-2xl bg-slate-800/80 flex items-center justify-center group-hover:scale-110 transition border border-slate-700/60 shadow-inner">
                <Upload className="w-8 h-8 text-sky-400" />
              </div>
              <div>
                <h3 className="font-bold text-base text-slate-100">Upload Your Squat Video</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Drag and drop any side-view video file here, or click to browse from your device.
                </p>
                <p className="text-[11px] text-slate-500 mt-1 font-mono">Supports MP4, MOV, AVI, WebM (up to 150MB)</p>
              </div>
              <label className="cursor-pointer px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 font-semibold text-xs transition shadow-md active:scale-95">
                Browse Video
                <input 
                  type="file" 
                  accept="video/*" 
                  className="hidden" 
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      startAnalysis(null, e.target.files[0]);
                    }
                  }} 
                />
              </label>
            </div>

            {/* Mini Filming Setup Card */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-sky-400 text-xs font-bold uppercase tracking-wider mb-3">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Filming Guidelines</span>
                </div>
                <h4 className="font-bold text-sm text-slate-200 mb-2">How to Record for 100% Accuracy</h4>
                <ul className="text-xs text-slate-400 space-y-2.5">
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <span><strong>90° Pure Side View</strong>: Perpendicular to your stance so the femur plane is not foreshortened.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <span><strong>Hip Height</strong>: Camera mounted at waist level (avoid bird-eye or floor-level tilts).</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <span><strong>Full Body in Frame</strong>: Keep head, barbell, and entire shoe sole visible throughout the set.</span>
                  </li>
                </ul>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800 text-[11px] text-slate-500">
                Grounded strictly in Mark Rippetoe's Starting Strength: Basic Barbell Training Ch. 2
              </div>
            </div>
          </section>
        )}

        {/* Real-time Job Progress Indicator */}
        {jobId && jobStatus !== 'DONE' && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center animate-pulse">
              <Activity className="w-7 h-7 text-sky-400 animate-spin" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Analyzing Your Squat Form</h3>
              <p className="text-xs text-slate-400 mt-1">{jobStage || "Extracting video properties..."}</p>
            </div>
            
            {/* Progress bar */}
            <div className="w-full max-w-md bg-slate-800 rounded-full h-3 overflow-hidden p-0.5 border border-slate-700">
              <div 
                className="bg-gradient-to-r from-sky-500 to-indigo-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${jobProgress}%` }}
              />
            </div>
            <span className="text-xs font-mono font-bold text-sky-400">{jobProgress}%</span>

            {jobError && (
              <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-4 py-2 rounded-lg max-w-md">
                Error: {jobError}
              </div>
            )}
          </section>
        )}

        {/* Results Presentation */}
        {results && (
          <div className="space-y-6">

            {/* Camera Perspective Error Alert if Frontal */}
            {results.evaluation?.global_issues?.length > 0 && (
              <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-5 space-y-2">
                {results.evaluation.global_issues.map((issue, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-bold text-rose-200">{issue.title}</h4>
                      <p className="text-xs text-rose-300/80 leading-relaxed mt-0.5">{issue.message}</p>
                      <p className="text-xs text-rose-200 font-semibold mt-1">👉 Fix for next set: {issue.actionable_cue}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Section 1: Consumer Form Score & Next-Set Action Cards */}
            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Form Score Card */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 flex flex-col items-center justify-center text-center relative overflow-hidden shadow-xl">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                  Overall Form Score
                </div>
                <div 
                  className="text-6xl font-black font-mono tracking-tighter"
                  style={{ color: results.consumer_summary?.grade_color || '#38bdf8' }}
                >
                  {results.consumer_summary?.score || 0}
                </div>
                <div 
                  className="text-sm font-extrabold uppercase tracking-wider mt-1 px-3 py-0.5 rounded-full bg-slate-800"
                  style={{ color: results.consumer_summary?.grade_color || '#38bdf8' }}
                >
                  {results.consumer_summary?.grade || 'ANALYZED'}
                </div>
                <p className="text-xs text-slate-300 mt-3 font-medium">
                  {results.consumer_summary?.headline}
                </p>

                {/* Form Checklist */}
                <div className="w-full mt-5 pt-4 border-t border-slate-800 space-y-2 text-left">
                  {results.consumer_summary?.checklist?.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-slate-950/40 border border-slate-800/60">
                      <div>
                        <div className="font-semibold text-slate-200">{item.name}</div>
                        <div className="text-[10px] text-slate-400">{item.note}</div>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        item.status === 'pass' 
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                          : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      }`}>
                        {item.status === 'pass' ? 'PASS' : 'FIX NEEDED'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Cards: What to Fix on Next Set */}
              <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Flame className="w-4 h-4 text-amber-400" />
                      <span>What to Fix on Your Next Set (Plain English)</span>
                    </h3>
                    <span className="text-xs text-slate-400">Zero Jargon Focus</span>
                  </div>
                  <div className="space-y-3">
                    {results.consumer_summary?.fixes?.map((fix, idx) => (
                      <div 
                        key={idx}
                        className={`p-4 rounded-xl border transition ${
                          fix.type === 'danger' 
                            ? 'bg-rose-500/10 border-rose-500/30 text-rose-100'
                            : fix.type === 'warning'
                            ? 'bg-amber-500/10 border-amber-500/30 text-amber-100'
                            : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-100'
                        }`}
                      >
                        <h4 className="font-bold text-sm flex items-center gap-2">
                          {fix.title}
                        </h4>
                        <p className="text-xs mt-1 leading-relaxed opacity-90">
                          {fix.desc}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Detected: <strong>{results.evaluation?.repetitions?.length || 0} Repetitions</strong></span>
                  <button
                    onClick={() => setResults(null)}
                    className="text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1"
                  >
                    Analyze Another Video <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </section>

            {/* Section 2: Synchronized Video & Canvas Overlay Studio */}
            <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-slate-800">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-sky-400" />
                    <span>Synchronized Video & Biomechanics Canvas</span>
                  </h3>
                  <p className="text-xs text-slate-400">Scrub video with live skeleton, midfoot balance axis, and depth plane overlays</p>
                </div>

                {/* Overlay Layer Toggles */}
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <button
                    onClick={() => setShowSkeleton(!showSkeleton)}
                    className={`px-2.5 py-1 rounded-lg border text-xs font-semibold transition ${
                      showSkeleton ? 'bg-sky-500/20 text-sky-300 border-sky-500/40' : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    Skeleton
                  </button>
                  <button
                    onClick={() => setShowMidfoot(!showMidfoot)}
                    className={`px-2.5 py-1 rounded-lg border text-xs font-semibold transition ${
                      showMidfoot ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    Midfoot Axis
                  </button>
                  <button
                    onClick={() => setShowBarTrail(!showBarTrail)}
                    className={`px-2.5 py-1 rounded-lg border text-xs font-semibold transition ${
                      showBarTrail ? 'bg-pink-500/20 text-pink-300 border-pink-500/40' : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    Bar Trail
                  </button>
                  <button
                    onClick={() => setShowDepthPlane(!showDepthPlane)}
                    className={`px-2.5 py-1 rounded-lg border text-xs font-semibold transition ${
                      showDepthPlane ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    Depth Plane
                  </button>
                </div>
              </div>

              {/* Video + Canvas Viewport */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Canvas Overlay Player */}
                <div className="relative aspect-[9/16] max-h-[560px] mx-auto rounded-xl overflow-hidden bg-black border border-slate-800 shadow-2xl flex items-center justify-center">
                  <video
                    ref={videoRef}
                    src={`/api/media/${results.annotated_filename || results.video_filename}`}
                    className="w-full h-full object-contain"
                    playsInline
                    loop
                    onTimeUpdate={() => {
                      if (videoRef.current) {
                        setCurrentTime(videoRef.current.currentTime);
                        setDuration(videoRef.current.duration || 0);
                      }
                    }}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                  />
                  <canvas
                    ref={canvasRef}
                    width={540}
                    height={960}
                    className="absolute inset-0 w-full h-full pointer-events-none object-contain"
                  />
                </div>

                {/* Player Controls & Rep Navigator */}
                <div className="flex flex-col justify-between space-y-4">
                  
                  {/* Transport Controls */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                      <span>{currentTime.toFixed(2)}s</span>
                      <span>{duration.toFixed(2)}s</span>
                    </div>

                    {/* Timeline seek bar */}
                    <input
                      type="range"
                      min={0}
                      max={duration || 10}
                      step={0.033}
                      value={currentTime}
                      onChange={(e) => seekToTime(parseFloat(e.target.value))}
                      className="w-full accent-sky-400 cursor-pointer"
                    />

                    {/* Buttons */}
                    <div className="flex items-center justify-between pt-1">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={togglePlay}
                          className="w-10 h-10 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 flex items-center justify-center font-bold transition active:scale-95 shadow-md shadow-sky-500/20"
                        >
                          {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
                        </button>
                        <button
                          onClick={() => stepFrame(false)}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700"
                        >
                          -1 Frame
                        </button>
                        <button
                          onClick={() => stepFrame(true)}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700"
                        >
                          +1 Frame
                        </button>
                      </div>

                      {/* Speed selector */}
                      <div className="flex items-center gap-1 text-xs">
                        <button
                          onClick={() => changeRate(0.5)}
                          className={`px-2 py-1 rounded font-mono ${playbackRate === 0.5 ? 'bg-sky-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'}`}
                        >
                          0.5x
                        </button>
                        <button
                          onClick={() => changeRate(1.0)}
                          className={`px-2 py-1 rounded font-mono ${playbackRate === 1.0 ? 'bg-sky-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'}`}
                        >
                          1.0x
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Clickable Rep Jump Markers */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-2.5">
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                      Click to Jump to Bottom Position
                    </h4>
                    <div className="grid grid-cols-2 gap-2">
                      {results.evaluation?.repetitions?.map((r) => {
                        const isBorder = r.depth_metrics?.is_borderline;
                        const isPass = r.depth_metrics?.meets_standard;
                        return (
                          <button
                            key={r.rep_id}
                            onClick={() => seekToTime(r.bottom_timestamp)}
                            className="p-2.5 rounded-xl border border-slate-800 hover:border-sky-500/40 bg-slate-900/60 text-left transition flex items-center justify-between group"
                          >
                            <div>
                              <div className="font-bold text-xs text-white">Rep {r.rep_id} Turnaround</div>
                              <div className="text-[10px] text-slate-400 font-mono">@{r.bottom_timestamp?.toFixed(2)}s</div>
                            </div>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              isBorder
                                ? 'bg-amber-500/20 text-amber-300'
                                : isPass
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : 'bg-rose-500/20 text-rose-300'
                            }`}>
                              {isBorder ? 'Borderline' : isPass ? 'Depth Pass' : 'High Squat'}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* VBT Quick KPI Glance */}
                  {results.evaluation?.set_vbt_summary && (
                    <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 grid grid-cols-3 gap-2 text-center">
                      <div>
                        <div className="text-[10px] text-slate-400 uppercase font-bold">Set Velocity</div>
                        <div className="text-base font-extrabold text-sky-400 font-mono">
                          {results.evaluation.set_vbt_summary.mean_set_velocity_mps?.toFixed(2) || '0.00'} m/s
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-400 uppercase font-bold">Fatigue Loss</div>
                        <div className="text-base font-extrabold text-amber-400 font-mono">
                          {results.evaluation.set_vbt_summary.total_velocity_loss_pct?.toFixed(0) || '0'}%
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-400 uppercase font-bold">Calibration</div>
                        <div className="text-base font-extrabold text-emerald-400 font-mono">
                          {results.evaluation.calibration?.px_per_cm?.toFixed(1) || '5.0'} px/cm
                        </div>
                      </div>
                    </div>
                  )}

                </div>
              </div>
            </section>

            {/* Section 3: Pro / Coach Mode Deep Analytics */}
            {proMode && (
              <section className="rounded-2xl border border-purple-900/40 bg-slate-900/90 p-6 space-y-6">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div>
                    <h3 className="text-lg font-bold text-purple-300 flex items-center gap-2">
                      <Activity className="w-5 h-5 text-purple-400" />
                      <span>Pro Coach Mode: Technical Biomechanics & Textbook Citations</span>
                    </h3>
                    <p className="text-xs text-slate-400">Detailed metric telemetry strictly grounded in Starting Strength Ch. 2</p>
                  </div>
                  <span className="text-xs font-mono px-2.5 py-1 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                    Engine: {results.evaluation?.evaluation_engine || 'Deterministic'}
                  </span>
                </div>

                {/* Rep Selection Tabs */}
                <div className="flex gap-2 border-b border-slate-800 pb-2">
                  {results.evaluation?.repetitions?.map((r) => (
                    <button
                      key={r.rep_id}
                      onClick={() => setActiveRepTab(r.rep_id)}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                        activeRepTab === r.rep_id
                          ? 'bg-purple-600 text-white shadow-md shadow-purple-600/20'
                          : 'bg-slate-800/60 text-slate-400 hover:text-white'
                      }`}
                    >
                      Repetition {r.rep_id}
                    </button>
                  ))}
                </div>

                {/* Findings Table for Active Rep */}
                {(() => {
                  const activeRep = results.evaluation?.repetitions?.find(r => r.rep_id === activeRepTab) || results.evaluation?.repetitions?.[0];
                  if (!activeRep) return null;

                  return (
                    <div className="space-y-4">
                      
                      {/* Biomechanics Metric Chips */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                          <div className="text-[10px] text-slate-400 uppercase font-bold">Back Angle</div>
                          <div className="text-base font-extrabold text-sky-400 font-mono">
                            {activeRep.back_angle?.bottom_angle_deg?.toFixed(1) || '0.0'}°
                          </div>
                          <div className="text-[10px] text-slate-500">Ref ~45° (Fig 2-13)</div>
                        </div>

                        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                          <div className="text-[10px] text-slate-400 uppercase font-bold">Depth Margin</div>
                          <div className={`text-base font-extrabold font-mono ${activeRep.depth?.meets_standard ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {activeRep.depth?.depth_margin_cm > 0 ? `+${activeRep.depth?.depth_margin_cm}` : activeRep.depth?.depth_margin_cm} cm
                          </div>
                          <div className="text-[10px] text-slate-500">Hip Crease vs Patella (Fig 2-1)</div>
                        </div>

                        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                          <div className="text-[10px] text-slate-400 uppercase font-bold">Bar Horizontal Drift</div>
                          <div className="text-base font-extrabold text-amber-400 font-mono">
                            {activeRep.bar_path?.max_drift_cm?.toFixed(1) || '0.0'} cm
                          </div>
                          <div className="text-[10px] text-slate-500">Midfoot Corridor (Fig 2-5)</div>
                        </div>

                        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                          <div className="text-[10px] text-slate-400 uppercase font-bold">Concentric Speed</div>
                          <div className="text-base font-extrabold text-purple-400 font-mono">
                            {activeRep.vbt?.mean_velocity_mps?.toFixed(2) || '0.00'} m/s
                          </div>
                          <div className="text-[10px] text-slate-500">Tempo: {activeRep.vbt?.tempo_notation}</div>
                        </div>
                      </div>

                      {/* Criteria Findings Grid */}
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                          Starting Strength Criteria Audit (Rep {activeRep.rep_id})
                        </h4>
                        
                        <div className="grid grid-cols-1 gap-3">
                          {activeRep.findings?.map((f, idx) => {
                            const isMeets = f.result === 'MEETS_STANDARD';
                            const isCannot = f.result === 'CANNOT_ASSESS';
                            return (
                              <div
                                key={idx}
                                className={`p-4 rounded-xl border transition ${
                                  isCannot
                                    ? 'bg-slate-950/60 border-slate-800 text-slate-300'
                                    : isMeets
                                    ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-100'
                                    : 'bg-rose-950/20 border-rose-500/30 text-rose-100'
                                }`}
                              >
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                  <div className="flex items-center gap-2">
                                    <span className="font-bold text-sm text-white">{f.criterion_name}</span>
                                    <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase bg-slate-800 text-slate-300">
                                      {f.category}
                                    </span>
                                  </div>
                                  <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${
                                    isCannot
                                      ? 'bg-slate-800 text-slate-300 border border-slate-700'
                                      : isMeets
                                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                  }`}>
                                    {f.result.replace(/_/g, ' ')}
                                  </span>
                                </div>

                                <div className="text-xs text-slate-400 mt-1 font-mono">
                                  Citation: {f.source_citation}
                                </div>

                                <p className="text-xs mt-2 leading-relaxed text-slate-200">
                                  {f.explanation}
                                </p>

                                {f.actionable_feedback && (
                                  <div className="mt-2 text-xs font-medium text-sky-300">
                                    💡 <strong>Coaching Cue</strong>: {f.actionable_feedback}
                                  </div>
                                )}

                                {f.uncertainty_and_limitations && (
                                  <div className="mt-1 text-[11px] text-slate-400 italic">
                                    ⚠️ {f.uncertainty_and_limitations}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>

                    </div>
                  );
                })()}

                {/* Non-Assessable Criteria Panel */}
                <div className="mt-6 pt-5 border-t border-slate-800">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                    Starting Strength Criteria That Cannot Be Assessed from a Side View
                  </h4>
                  <p className="text-xs text-slate-400 mb-3">
                    A sagittal side view is required for depth, back angle, and bar path, but the following criteria require a coronal or posterior filming angle:
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {results.evaluation?.non_assessable_side_view_criteria?.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                        <div className="font-bold text-slate-200">{item.criterion_name}</div>
                        <div className="text-[11px] text-slate-400 mt-1">{item.why_unassessable}</div>
                        <div className="text-[10px] text-slate-500 mt-1 font-mono">Refs: {item.source_ref_pages?.join(', ')}</div>
                      </div>
                    ))}
                  </div>
                </div>

              </section>
            )}

          </div>
        )}

      </main>

      {/* Standards Skill Modal */}
      {showStandardsModal && standardsData && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-base text-white">Starting Strength Skill Standards (JSON)</h3>
                <p className="text-xs text-slate-400">Decoupled rules engine v{standardsData.skill_version}</p>
              </div>
              <button
                onClick={() => setShowStandardsModal(false)}
                className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center text-sm font-bold"
              >
                ✕
              </button>
            </div>
            <div className="p-5 overflow-y-auto space-y-4 font-mono text-xs">
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 overflow-x-auto text-sky-300">
                {JSON.stringify(standardsData, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
        <p>IronPath AI • Grounded in Mark Rippetoe's Starting Strength: Basic Barbell Training</p>
      </footer>

    </div>
  );
}
