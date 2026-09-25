import React from 'react';

const Navbar: React.FC = () => {
  return (
    <div className="fixed top-6 left-4 right-4 z-50 flex justify-center pointer-events-none">
      <nav className="w-full max-w-[95%] lg:max-w-7xl bg-black border-2 border-white p-3 md:px-6 pointer-events-auto brutal-shadow-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-ridebid-green flex items-center justify-center font-bold text-black transform -skew-x-12">
            RB
          </div>
          <span className="text-xl font-bold tracking-widest text-white uppercase font-sans">
            RIDEBID
          </span>
        </div>
        
        <div className="flex items-center gap-6">
          <a href="#" className="hidden md:block text-sm font-bold uppercase tracking-widest hover:text-ridebid-green transition-colors">
            Docs
          </a>
          <button className="hidden md:flex w-8 h-8 items-center justify-center border-2 border-ridebid-green rounded-full hover:bg-ridebid-green hover:text-black transition-colors">
            <span className="text-xs font-mono">☼</span>
          </button>
          <a href="#" className="hidden md:block">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="hover:text-ridebid-green transition-colors">
              <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
            </svg>
          </a>
          <button className="bg-white text-black font-bold uppercase tracking-widest px-6 py-2 brutal-shadow-hover transition-all border-2 border-transparent hover:border-black font-mono">
            Try Now
          </button>
        </div>
      </nav>
    </div>
  );
};

export default Navbar;
