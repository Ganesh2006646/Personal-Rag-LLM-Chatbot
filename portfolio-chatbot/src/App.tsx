import ChatWidget from './components/ChatWidget';
import { Terminal, Shield, Cpu, RefreshCw, Layers, Award, BookOpen } from 'lucide-react';

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 selection:bg-cyan-500 selection:text-black font-sans">
      
      {/* Background Gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-900/20 via-gray-950 to-gray-950 pointer-events-none z-0"></div>

      {/* Navigation Header */}
      <header className="relative z-10 border-b border-gray-900/60 bg-gray-950/40 backdrop-blur-md px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono font-bold text-lg text-white">
            <Terminal className="h-5 w-5 text-cyan-400" />
            <span>GANESH_GIRIDHAR.sh</span>
          </div>
          <div className="flex items-center gap-6 text-sm font-mono text-gray-400">
            <a href="https://github.com/ganeshgiridhar" target="_blank" rel="noreferrer" className="hover:text-cyan-400 flex items-center gap-1 transition-colors">
              <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg> GitHub
            </a>
            <span className="h-4 w-[1px] bg-gray-800"></span>
            <span className="text-cyan-400 flex items-center gap-1 animate-pulse">
              <span className="h-2 w-2 rounded-full bg-cyan-500"></span> AI Agent Active
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="relative z-10 max-w-6xl mx-auto px-6 py-12 space-y-16">
        
        {/* Hero Section */}
        <section className="space-y-6 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/40 border border-cyan-800/30 text-cyan-400 font-mono text-xs">
            <Shield className="h-3.5 w-3.5" /> Systems Architect & AI Builder
          </div>
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            I build systems that function <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">honestly</span> and scale.
          </h1>
          <p className="text-gray-400 text-lg leading-relaxed">
            I'm Ganesh, a B.Tech CSE student at Amrita Coimbatore. I specialize in offline-first mobile apps, agentic AI execution loops, and workflow automation. I think in abstractions, design for constraints, and execute linearly.
          </p>
        </section>

        {/* Flagship Projects Section */}
        <section className="space-y-6">
          <h2 className="text-xl font-bold tracking-wider text-gray-400 uppercase font-mono flex items-center gap-2">
            <Layers className="h-5 w-5 text-blue-500" /> Featured Architectures
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Project 1 */}
            <div className="group relative rounded-2xl bg-gray-900/30 border border-gray-800 p-6 space-y-4 hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(6,182,212,0.1)] transition-all duration-300">
              <div className="flex items-center justify-between">
                <div className="font-mono text-xs text-cyan-400 bg-cyan-950/40 px-2.5 py-0.5 rounded border border-cyan-950">
                  Flutter + SQLite/Drift
                </div>
                <Award className="h-5 w-5 text-yellow-500" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors">RiceAgent Pro</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Offline-first operations platform for wholesale rice distribution. Features transaction queues and robust server merge-sync architectures.
              </p>
              <div className="flex items-center gap-1.5 text-xs text-gray-500 pt-2 font-mono">
                <RefreshCw className="h-3 w-3 animate-spin-slow" /> Offline Sync • WhatsApp API
              </div>
            </div>

            {/* Project 2 */}
            <div className="group relative rounded-2xl bg-gray-900/30 border border-gray-800 p-6 space-y-4 hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(6,182,212,0.1)] transition-all duration-300">
              <div className="flex items-center justify-between">
                <div className="font-mono text-xs text-cyan-400 bg-cyan-950/40 px-2.5 py-0.5 rounded border border-cyan-950">
                  FastAPI + Docker
                </div>
                <Cpu className="h-5 w-5 text-blue-500" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors">ExecuCode</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                AI code-grading agent loop running execution units inside sandboxed, resource-limited Docker containers for deterministic evaluations.
              </p>
              <div className="flex items-center gap-1.5 text-xs text-gray-500 pt-2 font-mono">
                <Terminal className="h-3 w-3" /> Sandboxed Sandbox • AST Analysis
              </div>
            </div>

            {/* Project 3 */}
            <div className="group relative rounded-2xl bg-gray-900/30 border border-gray-800 p-6 space-y-4 hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(6,182,212,0.1)] transition-all duration-300">
              <div className="flex items-center justify-between">
                <div className="font-mono text-xs text-cyan-400 bg-cyan-950/40 px-2.5 py-0.5 rounded border border-cyan-950">
                  Java + JavaFX
                </div>
                <BookOpen className="h-5 w-5 text-cyan-500" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors">FLIP WARS</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                JavaFX board game visualizer driven by Alpha-Beta Minimax search tree pruning, Zobrist transposition hashing, and graph DFS components.
              </p>
              <div className="flex items-center gap-1.5 text-xs text-gray-500 pt-2 font-mono">
                <span>0.2s Minimax • Zobrist State Hashing</span>
              </div>
            </div>

          </div>
        </section>

        {/* Live System Showcase Callout */}
        <section className="rounded-2xl border border-gray-800/80 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-blue-950/30 via-gray-950 to-gray-950 p-8 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Terminal className="h-5 w-5 text-cyan-400" /> Try the Portfolio Intelligence Agent
              </h3>
              <p className="text-gray-400 text-sm max-w-xl">
                The floating assistant in the bottom-right is directly connected to my personal RAG database. It queries structured files on my psychology, education, and source codes to answer recruiter queries in real-time.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-ping"></span>
              <span className="text-xs font-mono text-gray-400">Database connected via Qdrant Cloud</span>
            </div>
          </div>
        </section>

      </main>

      {/* Floating Chat Widget Component */}
      <ChatWidget />
    </div>
  );
}
