import React, { useState, useMemo } from 'react';
import { UploadCloud, FileText, Briefcase, CheckCircle, XCircle, ArrowRight, BrainCircuit, RotateCw, Github, Linkedin, Twitter } from 'lucide-react';

const App = () => {
    const [resume, setResume] = useState(null);
    const [jobDescription, setJobDescription] = useState("");
    const [matchResult, setMatchResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    
    // !!! IMPORTANT: Replace this with your actual backend URL from Railway or DigitalOcean !!!
    const API_URL = "smart-resume-matcher-production.up.railway.app"; 

    const handleFileChange = (files) => {
        if (files && files[0] && files[0].type === "application/pdf" && files[0].size < 5 * 1024 * 1024) {
            setResume(files[0]);
            setError(null);
            setMatchResult(null);
        } else {
            setError("Please upload a PDF file smaller than 5MB.");
        }
    };

    const handleSubmit = async () => {
        if (!resume || !jobDescription) return setError("Please provide a resume and job description.");
        if (API_URL.includes("your-backend-url")) return setError("Please update the API_URL in src/App.js");
        
        setIsLoading(true);
        setError(null);
        setMatchResult(null);

        const formData = new FormData();
        formData.append('file', resume);
        formData.append('job_description', jobDescription);
        
        try {
            const response = await fetch(`${API_URL}/api/calculate-match`, { method: 'POST', body: formData });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "An error occurred during analysis.");
            }
            setMatchResult(await response.json());
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };
    
    const scoreColor = useMemo(() => {
        if (!matchResult) return 'text-slate-800';
        if (matchResult.score >= 85) return 'text-emerald-500';
        if (matchResult.score >= 70) return 'text-amber-500';
        return 'text-red-500';
    }, [matchResult]);
    
    const handleDragEnter = (e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); };
    const handleDragLeave = (e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); };
    const handleDragOver = (e) => { e.preventDefault(); e.stopPropagation(); };
    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        handleFileChange(e.dataTransfer.files);
    };

    return (
        <div className="min-h-screen bg-slate-50 font-sans text-slate-800">
            <div className="container mx-auto px-4 py-8 md:py-16">
                <header className="text-center mb-12 md:mb-16">
                    <div className="inline-flex items-center gap-3 mb-4">
                        <BrainCircuit className="h-10 w-10 text-indigo-600" />
                        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-slate-900">Smart Resume Matcher</h1>
                    </div>
                    <p className="text-lg md:text-xl text-slate-600 max-w-3xl mx-auto">
                        Upload your resume and paste a job description to get an AI-powered compatibility score in seconds.
                    </p>
                </header>
                
                <main className="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12 items-start">
                    <div className="bg-white p-6 md:p-8 rounded-2xl shadow-lg border border-slate-200 space-y-8">
                        <div>
                            <h2 className="text-2xl font-semibold flex items-center gap-3 mb-4">
                                <FileText className="text-indigo-600" /> Your Resume
                            </h2>
                            <div 
                                onDragEnter={handleDragEnter} onDragLeave={handleDragLeave} onDragOver={handleDragOver} onDrop={handleDrop}
                                className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${isDragging ? 'border-indigo-600 bg-indigo-50' : 'border-slate-300 hover:border-indigo-500'}`}>
                                <input type="file" id="resume-upload" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" onChange={(e) => handleFileChange(e.target.files)} accept=".pdf" />
                                <UploadCloud className="mx-auto h-12 w-12 text-slate-400 mb-4" />
                                <label htmlFor="resume-upload" className="font-semibold text-indigo-600 cursor-pointer">Click to upload</label>
                                <p className="text-sm text-slate-500 mt-1">or drag and drop PDF (max 5MB)</p>
                            </div>
                            {resume && (
                                <div className="mt-4 bg-slate-100 p-3 rounded-lg flex items-center justify-between">
                                    <div className="flex items-center gap-3 overflow-hidden">
                                        <FileText className="h-5 w-5 text-indigo-600 flex-shrink-0" />
                                        <span className="text-sm font-medium text-slate-700 truncate">{resume.name}</span>
                                    </div>
                                    <button onClick={() => setResume(null)} className="text-slate-500 hover:text-red-500 transition-colors"><XCircle className="h-5 w-5" /></button>
                                </div>
                            )}
                        </div>
                        <div>
                            <h2 className="text-2xl font-semibold flex items-center gap-3 mb-4"><Briefcase className="text-indigo-600" /> Job Description</h2>
                            <textarea
                                value={jobDescription}
                                onChange={(e) => { setJobDescription(e.target.value); setMatchResult(null); }}
                                placeholder="Paste the full job description here..."
                                className="w-full h-48 p-4 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow duration-200 resize-y"
                            />
                        </div>
                        <button
                            onClick={handleSubmit} disabled={isLoading || !resume || !jobDescription}
                            className="w-full bg-indigo-600 text-white font-bold py-4 px-6 rounded-xl text-lg flex items-center justify-center gap-3 hover:bg-indigo-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 shadow-md hover:shadow-lg focus:outline-none focus:ring-4 focus:ring-indigo-300">
                            {isLoading ? (<><RotateCw className="animate-spin h-6 w-6" /> Analyzing...</>) : (<>Calculate Match <ArrowRight className="h-6 w-6" /></>)}
                        </button>
                    </div>
                    <div className="bg-white p-6 md:p-8 rounded-2xl shadow-lg border border-slate-200 min-h-[30rem] flex flex-col justify-center">
                        {error && <div className="text-center text-red-600 bg-red-100 p-4 rounded-lg">{error}</div>}
                        {!matchResult && !isLoading && !error && (
                            <div className="text-center text-slate-500">
                                <BrainCircuit className="h-16 w-16 mx-auto mb-4 text-slate-400" />
                                <h3 className="text-xl font-semibold mb-2">Awaiting Analysis</h3>
                                <p>Your match results will appear here.</p>
                            </div>
                        )}
                        {isLoading && (
                           <div className="text-center text-slate-600">
                               <div className="relative w-24 h-24 mx-auto mb-6">
                                   <div className="absolute inset-0 border-4 border-indigo-200 rounded-full"></div>
                                   <div className="absolute inset-0 border-t-4 border-indigo-600 rounded-full animate-spin"></div>
                               </div>
                               <h3 className="text-xl font-semibold mb-2 animate-pulse">AI is thinking...</h3>
                               <p>Analyzing skills and experience.</p>
                           </div>
                        )}
                        {matchResult && (
                            <div className="animate-fade-in space-y-8">
                                <div>
                                    <h2 className="text-center text-2xl font-semibold text-slate-800 mb-4">Compatibility Score</h2>
                                    <div className="relative w-40 h-40 mx-auto">
                                        <svg className="w-full h-full" viewBox="0 0 36 36">
                                            <path className="text-slate-200" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3"></path>
                                            <path className={`${scoreColor.replace('text-', 'stroke-')}`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" strokeDasharray={`${matchResult.score}, 100`} strokeDashoffset="0" transform="rotate(-90 18 18)"></path>
                                        </svg>
                                        <div className={`absolute inset-0 flex items-center justify-center text-5xl font-bold ${scoreColor}`}>
                                            {Math.round(matchResult.score)}<span className="text-2xl mt-1">%</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="bg-emerald-50/70 p-4 rounded-xl border border-emerald-200">
                                        <h3 className="text-lg font-semibold flex items-center gap-2 text-emerald-800 mb-3"><CheckCircle /> Matched Skills</h3>
                                        <ul className="flex flex-wrap gap-2">
                                            {matchResult.matched_skills.map(skill => (<li key={skill} className="bg-emerald-100 text-emerald-900 text-sm font-medium px-3 py-1 rounded-full">{skill}</li>))}
                                        </ul>
                                    </div>
                                    <div className="bg-amber-50/70 p-4 rounded-xl border border-amber-200">
                                        <h3 className="text-lg font-semibold flex items-center gap-2 text-amber-800 mb-3"><XCircle /> Areas for Improvement</h3>
                                        <ul className="flex flex-wrap gap-2">
                                            {matchResult.missing_skills.map(skill => (<li key={skill} className="bg-amber-100 text-amber-900 text-sm font-medium px-3 py-1 rounded-full">{skill}</li>))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </main>
                <footer className="text-center mt-16 text-slate-500">
                    <p className="mb-2">Built with a Hybrid AI approach.</p>
                     <div className="flex justify-center gap-6">
                        <a href="#" className="hover:text-indigo-600 transition-colors"><Github /></a>
                        <a href="#" className="hover:text-indigo-600 transition-colors"><Linkedin /></a>
                        <a href="#" className="hover:text-indigo-600 transition-colors"><Twitter /></a>
                    </div>
                </footer>
            </div>
            <style>{`
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
                body { font-family: 'Inter', sans-serif; }
                @keyframes fade-in { 0% { opacity: 0; transform: translateY(10px); } 100% { opacity: 1; transform: translateY(0); } }
                .animate-fade-in { animation: fade-in 0.5s ease-out forwards; }
            `}</style>
        </div>
    );
};
export default App;