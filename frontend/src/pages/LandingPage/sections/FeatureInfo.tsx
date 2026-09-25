import React from 'react';

const FeatureInfo: React.FC = () => {
  return (
    <section className="bg-ridebid-green py-24 px-4 overflow-hidden">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-16 relative">
        
        {/* Background decorative symbols */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-20 flex justify-around items-center">
          <div className="text-[20rem] font-sans font-extrabold text-black transform rotate-12">%</div>
          <div className="text-[20rem] font-sans font-extrabold text-black transform -rotate-12">+</div>
          <div className="text-[20rem] font-sans font-extrabold text-black transform rotate-6">$</div>
        </div>

        {/* Left Column */}
        <div className="flex-1 relative z-10">
          <div className="inline-block bg-white border-2 border-transparent text-black font-mono text-sm font-bold px-4 py-2 brutal-shadow mb-12">
            <span className="text-ridebid-green mr-2">■</span>
            THE MISSING AGGREGATOR FOR RIDEBID
          </div>
          
          <div className="text-black font-mono text-xs font-bold uppercase tracking-[0.2em] mb-6">
            MANDATORY CRINGE TAGLINE ON A LANDING PAGE
          </div>
          
          <h2 className="text-6xl md:text-8xl font-black text-black leading-[0.85] tracking-tight uppercase">
            DRIVERS GET <br />
            THE CASH. <br />
            <span className="text-transparent" style={{ WebkitTextStroke: '2px black' }}>
              WE DO THE
            </span> <br />
            REST.
          </h2>
        </div>

        {/* Right Column (Info Box) */}
        <div className="flex-1 relative z-10 pt-12 lg:pt-0">
          {/* Header Tag */}
          <div className="absolute top-8 right-8 z-20 transform rotate-3">
            <div className="bg-ridebid-green text-black border-2 border-white font-mono font-bold text-sm px-3 py-1 brutal-shadow-white">
              // NO CRON JOBS
            </div>
          </div>

          <div className="bg-black border-2 border-white p-10 brutal-shadow-white mt-12 relative">
            <h3 className="text-white font-sans text-2xl md:text-3xl font-bold uppercase leading-snug mb-8">
              RIDEBID IS GREAT AT CHECKOUT.<br />
              TOO BAD YOU CAN'T MAKE THE<br />
              USER PAY FOR EACH AND EVERY<br />
              REQUEST THEY SEND.<br />
              AT LEAST NOT MONETARILY. 🤪
            </h3>
            
            <div className="border-l-4 border-ridebid-green pl-6 text-gray-300 font-mono text-sm leading-relaxed space-y-4">
              <p>
                Instead of writing an entire data ingestion pipeline to keep track of payments and sync to drivers, just fire your events to RideBid.
              </p>
              <p>
                We hook into your existing account (you keep full control of the money) and aggregate the usage, evaluate your weird pricing logic and bill the customer at the end of the month.
              </p>
            </div>
            
            {/* Decorative Label */}
            <div className="absolute -bottom-5 -left-5 transform -rotate-2">
              <div className="bg-fuchsia-500 text-black border-2 border-black font-mono font-bold text-sm px-4 py-2 brutal-shadow">
                NO DB MIGRATIONS
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeatureInfo;
