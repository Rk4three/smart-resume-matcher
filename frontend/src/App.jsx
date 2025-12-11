import React, { useState, useRef } from 'react';
import { Upload, CheckCircle, AlertCircle, X, Briefcase, ChevronRight, Sparkles, TrendingUp, Award, Target, Layers } from 'lucide-react';

const API_URL = 'https://smart-resume-matcher-h1kd.onrender.com';

function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [matchResult, setMatchResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    if (file.type === "application/pdf") {
      setFile(file);
      setError(null);
    } else {
      setError("Please upload a PDF file.");
    }
  };

  const handleSubmit = async () => {
    if (!file || !jobDescription) {
      setError("Please provide both a resume and job description.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setMatchResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_description', jobDescription);

    try {
      const response = await fetch(`${API_URL}/api/calculate-match`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setMatchResult(data);
    } catch (err) {
      console.error(err);
      setError("Failed to analyze. Ensure the backend is running on port 8000.");
    } finally {
      setIsLoading(false);
    }
  };

  const clearFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score) => {
    if (score >= 80) return 'bg-green-50 border-green-200';
    if (score >= 60) return 'bg-blue-50 border-blue-200';
    if (score >= 40) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-600 rounded-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Smart Resume Matcher</h1>
              <p className="text-sm text-gray-600">AI-powered resume analysis with skill category matching</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Input Section */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Resume Upload */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Upload Resume (PDF)
            </label>

            {file ? (
              <div className="flex items-center justify-between p-4 bg-indigo-50 border-2 border-indigo-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                  <div>
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-600">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <button
                  onClick={clearFile}
                  className="p-2 hover:bg-indigo-100 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            ) : (
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                  dragActive
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
                }`}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-1">Drag & drop your PDF here</p>
                <p className="text-sm text-gray-500">or click to browse files</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleChange}
                  className="hidden"
                />
              </div>
            )}
          </div>

          {/* Job Description */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Job Description
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the full job description here..."
              className="w-full h-48 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
            />
          </div>
        </div>

        {/* Analyze Button */}
        <div className="text-center mb-8">
          <button
            onClick={handleSubmit}
            disabled={!file || !jobDescription || isLoading}
            className="px-8 py-4 bg-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all transform hover:scale-105 disabled:transform-none"
          >
            {isLoading ? (
              <>
                <span className="inline-block animate-spin mr-2">⚙️</span>
                Analyzing with AI...
              </>
            ) : (
              <>
                <Sparkles className="inline w-5 h-5 mr-2" />
                Analyze Match
              </>
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Results Section */}
        {matchResult && (
          <div className="space-y-6">
            {/* Score Card */}
            <div className={`rounded-xl shadow-lg border-2 p-8 ${getScoreBgColor(matchResult.score)}`}>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-700 mb-2">Match Score</h2>
                  <p className={`text-6xl font-bold ${getScoreColor(matchResult.score)}`}>
                    {matchResult.score}%
                  </p>
                  {matchResult.breakdown && (
                    <div className="mt-4 space-y-2 text-sm text-gray-600">
                      <div className="flex items-center gap-4">
                        <div>
                          <p className="font-medium">Required Skills</p>
                          <p>{matchResult.breakdown.required_match}</p>
                        </div>
                        <div>
                          <p className="font-medium">Preferred Skills</p>
                          <p>{matchResult.breakdown.preferred_match}</p>
                        </div>
                      </div>
                      {matchResult.breakdown.category_matches > 0 && (
                        <div className="flex items-center gap-2 text-indigo-700">
                          <Layers className="w-4 h-4" />
                          <p>{matchResult.breakdown.category_matches} category-based matches</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div className="text-6xl">
                  {matchResult.score >= 80 ? '🎯' : matchResult.score >= 60 ? '👍' : '📊'}
                </div>
              </div>
            </div>

            {/* Suggestions */}
            {matchResult.suggestions && matchResult.suggestions.length > 0 && (
              <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
                <div className="flex items-start gap-3">
                  <Award className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-blue-900 mb-2">Insights</h3>
                    <ul className="space-y-2">
                      {matchResult.suggestions.map((suggestion, idx) => (
                        <li key={idx} className="text-blue-800 flex items-start gap-2">
                          <ChevronRight className="w-4 h-4 flex-shrink-0 mt-1" />
                          <span>{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Skills Grid */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Matched Required Skills */}
              {matchResult.matched_skills && matchResult.matched_skills.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <h3 className="font-semibold text-gray-900">Matched Required Skills</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {matchResult.matched_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 bg-green-100 text-green-800 rounded-full text-sm font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Matched Preferred Skills */}
              {matchResult.matched_preferred && matchResult.matched_preferred.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Target className="w-5 h-5 text-blue-600" />
                    <h3 className="font-semibold text-gray-900">Matched Preferred Skills</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {matchResult.matched_preferred.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Missing Skills */}
              {matchResult.missing_critical && matchResult.missing_critical.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <AlertCircle className="w-5 h-5 text-orange-600" />
                    <h3 className="font-semibold text-gray-900">Skills to Consider</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {matchResult.missing_critical.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 bg-orange-100 text-orange-800 rounded-full text-sm font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!matchResult && !isLoading && !error && (
          <div className="text-center py-16 bg-white rounded-xl shadow-sm border border-gray-200">
            <Briefcase className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">Upload a resume and paste a job description to get started</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;