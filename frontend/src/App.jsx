import React, { useState, useEffect } from 'react';

export default function App() {
  const [activeTab, setActiveTab] = useState('pipeline');
  const [url, setUrl] = useState('');
  const [selectedSteps, setSelectedSteps] = useState(['download', 'transcribe', 'translate', 'subtitle', 'dub']);
  const [position, setPosition] = useState('top-right');
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [apiKeys, setApiKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState(null);

  const toggleStep = (step) => {
    if (selectedSteps.includes(step)) {
      setSelectedSteps(selectedSteps.filter(s => s !== step));
    } else {
      setSelectedSteps([...selectedSteps, step]);
    }
  };

  const handleStartPipeline = async (e) => {
    e.preventDefault();
    if (!url) return;

    setIsProcessing(true);
    try {
      const res = await fetch('/api/v1/pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          steps: selectedSteps,
          options: {
            quality: 'best',
            subtitle_style: { position: 'bottom' },
            dub: { voice: 'female', mix_mode: 'overlay' }
          }
        })
      });
      const data = await res.json();
      setJobId(data.job_id);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (!jobId || !isProcessing) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/jobs/${jobId}`);
        const data = await res.json();
        setJobStatus(data);
        if (data.status === 'done' || data.status === 'failed') {
          setIsProcessing(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error(err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId, isProcessing]);

  const handleCreateApiKey = async () => {
    if (!newKeyName) return;
    try {
      const res = await fetch('/api/v1/admin/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newKeyName })
      });
      const data = await res.json();
      setCreatedKey(data.api_key);
      setNewKeyName('');
      fetchApiKeys();
    } catch (err) {
      console.error(err);
    }
  };

  const fetchApiKeys = async () => {
    try {
      const res = await fetch('/api/v1/admin/keys');
      const data = await res.json();
      setApiKeys(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (activeTab === 'admin') fetchApiKeys();
  }, [activeTab]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-10 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl btn-gradient flex items-center justify-center font-bold text-xl text-white shadow-lg">
            ⚡
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Downloader Ultimate</h1>
            <p className="text-xs text-slate-400">TikTok / Douyin Video Processing & AI Dubbing Engine</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex gap-2 bg-slate-900 p-1.5 rounded-xl border border-slate-800">
          {['pipeline', 'history', 'admin', 'docs'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </header>

      {/* Main Content Area */}
      <main>
        {activeTab === 'pipeline' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Form Column */}
            <div className="lg:col-span-2 space-y-6">
              <div className="glass-card rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <span>🎬</span> Video Pipeline Config
                </h2>

                <form onSubmit={handleStartPipeline} className="space-y-5">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                      TikTok / Douyin Video URL
                    </label>
                    <input
                      type="url"
                      placeholder="https://www.tiktok.com/@user/video/..."
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      required
                      className="w-full bg-slate-900/80 border border-slate-700/60 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                    />
                  </div>

                  {/* Processing Steps Selection */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                      Select Processing Steps
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {[
                        { id: 'download', label: '⬇️ Download' },
                        { id: 'transcribe', label: '🎙️ STT (Whisper)' },
                        { id: 'translate', label: '🌐 Translate (VI)' },
                        { id: 'subtitle', label: '💬 Burn Subtitle' },
                        { id: 'dub', label: '🗣️ AI Dubbing' },
                        { id: 'logo', label: '🖼️ Watermark Logo' },
                      ].map((step) => (
                        <button
                          key={step.id}
                          type="button"
                          onClick={() => toggleStep(step.id)}
                          className={`px-3 py-2.5 rounded-xl border text-xs font-medium transition text-left flex items-center justify-between ${
                            selectedSteps.includes(step.id)
                              ? 'bg-indigo-600/20 border-indigo-500 text-indigo-200'
                              : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:border-slate-700'
                          }`}
                        >
                          <span>{step.label}</span>
                          {selectedSteps.includes(step.id) && <span className="text-indigo-400">✓</span>}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 9-Grid Position Picker */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                      Logo Overlay Position
                    </label>
                    <div className="grid grid-cols-3 gap-2 w-48 bg-slate-900 p-2 rounded-xl border border-slate-800">
                      {['top-left', 'center', 'top-right', 'center', 'center', 'center', 'bottom-left', 'center', 'bottom-right'].map((pos, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setPosition(pos)}
                          className={`h-8 rounded-lg text-xs font-bold transition ${
                            position === pos
                              ? 'bg-pink-600 text-white'
                              : 'bg-slate-800 text-slate-500 hover:bg-slate-700'
                          }`}
                        >
                          {pos === 'top-left' ? 'TL' : pos === 'top-right' ? 'TR' : pos === 'bottom-left' ? 'BL' : pos === 'bottom-right' ? 'BR' : '•'}
                        </button>
                      ))}
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isProcessing}
                    className="w-full btn-gradient py-3.5 rounded-xl text-white font-semibold shadow-lg disabled:opacity-50"
                  >
                    {isProcessing ? 'Processing Video...' : '🚀 Start Full Pipeline'}
                  </button>
                </form>
              </div>
            </div>

            {/* Realtime Progress Column */}
            <div className="space-y-6">
              <div className="glass-card rounded-2xl p-6">
                <h3 className="text-md font-semibold text-white mb-4">Live Status Monitor</h3>

                {jobStatus ? (
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-slate-400 capitalize">Status: {jobStatus.status}</span>
                        <span className="text-indigo-400 font-semibold">{jobStatus.progress}%</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-pink-500 h-2.5 transition-all duration-500"
                          style={{ width: `${jobStatus.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    {jobStatus.output_url && (
                      <div className="pt-4 border-t border-slate-800">
                        <a
                          href={jobStatus.output_url}
                          target="_blank"
                          rel="noreferrer"
                          className="block w-full bg-emerald-600 hover:bg-emerald-500 text-center py-2.5 rounded-xl text-xs font-bold text-white transition"
                        >
                          ⬇️ Download Result Video
                        </a>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500 text-xs">
                    No active job. Submit URL above to begin monitoring.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'admin' && (
          <div className="glass-card rounded-2xl p-6 space-y-6">
            <h2 className="text-lg font-semibold text-white">API Key Management</h2>

            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Key Name (e.g. n8n Production)"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-sm text-white"
              />
              <button
                onClick={handleCreateApiKey}
                className="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-xl text-sm font-semibold text-white"
              >
                Create Key
              </button>
            </div>

            {createdKey && (
              <div className="p-4 bg-emerald-950/60 border border-emerald-800 rounded-xl text-xs text-emerald-300">
                Created Key: <code className="font-bold">{createdKey}</code>
              </div>
            )}

            <div className="divide-y divide-slate-800">
              {apiKeys.map((k) => (
                <div key={k.key_id} className="py-3 flex justify-between items-center text-xs">
                  <div>
                    <div className="font-semibold text-white">{k.name}</div>
                    <div className="text-slate-500">{k.key_id}</div>
                  </div>
                  <span className={`px-2 py-1 rounded ${k.is_active ? 'bg-emerald-900/60 text-emerald-300' : 'bg-rose-900/60 text-rose-300'}`}>
                    {k.is_active ? 'Active' : 'Revoked'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
