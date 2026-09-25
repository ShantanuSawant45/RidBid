import React from 'react';

const HeroSection: React.FC = () => {
  return (
    <section className="relative min-h-screen pt-32 pb-20 px-4 flex items-center bg-ridebid-black overflow-hidden bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-neutral-900 to-ridebid-black">
      {/* Decorative Grid Background */}
      <div className="absolute inset-0 opacity-10 pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#4f772d 1px, transparent 1px), linear-gradient(90deg, #4f772d 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
      </div>

      <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-12 lg:gap-8 items-center relative z-10">
        
        {/* Left Column: Typography */}
        <div className="flex flex-col items-start gap-6">
          <div className="inline-block bg-white text-black font-mono text-xs font-bold px-3 py-1 border-2 border-black brutal-shadow mb-4">
            // RIDE BIDDING SYSTEM
          </div>
          
          <h1 className="text-6xl md:text-8xl lg:text-9xl font-extrabold leading-[0.85] tracking-tight uppercase text-white font-sans">
            BOOK <br />
            YOUR <br />
            OWN <br />
            PRICE <br />
            <span className="bg-ridebid-green text-black px-2 inline-block mt-4 brutal-shadow-white transform -rotate-1">
              IN REAL-TIME.
            </span>
          </h1>

          <div className="absolute top-[40%] left-[25%] hidden lg:block transform rotate-6 z-20">
            <div className="bg-black text-white font-mono text-xs border-2 border-white px-3 py-1 flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
              DRAG ME PLEASE...
            </div>
          </div>
        </div>

        {/* Right Column: Code Window */}
        <div className="relative w-full max-w-lg mx-auto lg:mr-0 transform lg:rotate-2">
          {/* Status Sticker */}
          <div className="absolute -right-6 top-1/4 z-30 transform rotate-12">
            <div className="bg-black border-2 border-white p-3 text-center w-28 brutal-shadow-white">
              <div className="text-ridebid-green text-2xl font-bold mb-1">*</div>
              <div className="text-[10px] font-mono text-white tracking-widest">STATUS: READY</div>
            </div>
          </div>

          <div className="bg-black border-2 border-ridebid-green brutal-shadow w-full">
            {/* Window Header */}
            <div className="bg-ridebid-green p-3 flex items-center justify-between border-b-2 border-ridebid-green">
              <div className="flex gap-2">
                <div className="w-3 h-3 border-2 border-black bg-white"></div>
                <div className="w-3 h-3 border-2 border-black bg-black"></div>
              </div>
              <div className="text-black font-mono text-xs font-bold uppercase tracking-widest">
                booking.ts
              </div>
              <div className="text-black font-bold font-mono border-2 border-black px-1 leading-none hover:bg-black hover:text-ridebid-green cursor-pointer">
                &gt;_
              </div>
            </div>
            
            {/* Window Body */}
            <div className="p-6 font-mono text-sm leading-relaxed overflow-x-auto text-gray-300">
              <div className="text-gray-500 mb-4">
                // No more static pricing nightmares.<br/>
                // Just bid, match & ride.
              </div>
              <div>
                <span className="text-purple-400">import</span> {'{ ridebid }'} <span className="text-purple-400">from</span> <span className="text-green-400">"@ridebid/core"</span>
              </div>
              <br/>
              <div>
                <span className="text-purple-400">const</span> client = ridebid({'{'}<br/>
                &nbsp;&nbsp;apiKey: process.env.RIDEBID_KEY,<br/>
                &nbsp;&nbsp;baseURL: <span className="text-green-400">"https://api.ridebid.com"</span>,<br/>
                {'}'})
              </div>
              <br/>
              <div>
                <span className="text-purple-400">await</span> client.<span className="text-yellow-400">placeBid</span>({'{'}<br/>
                &nbsp;&nbsp;userId: <span className="text-green-400">"usr_123"</span>,<br/>
                &nbsp;&nbsp;route: <span className="text-green-400">"JFK_TO_MANHATTAN"</span>,<br/>
                &nbsp;&nbsp;offer: <span className="text-orange-400">4500</span>, <span className="text-gray-500">// In cents</span><br/>
                {'}'})
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
};

export default HeroSection;
