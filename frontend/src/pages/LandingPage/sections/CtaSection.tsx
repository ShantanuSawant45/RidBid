import React from 'react';

const CtaSection: React.FC = () => {
  return (
    <section className="bg-black py-32 px-4 relative border-t-4 border-white overflow-hidden">
      {/* Decorative Background Elements */}
      <div className="absolute top-10 left-10 text-ridebid-green opacity-20 font-mono text-9xl pointer-events-none transform -rotate-12">
        {'//'}
      </div>
      <div className="absolute bottom-10 right-10 text-white opacity-10 font-sans font-black text-[15rem] leading-none pointer-events-none">
        GO
      </div>

      <div className="max-w-6xl mx-auto relative z-10">
        <div className="text-center mb-20">
          <div className="inline-block bg-ridebid-green text-black font-mono font-bold px-4 py-2 border-2 border-white brutal-shadow-white mb-6 transform -rotate-2">
            TIME TO MAKE A CHOICE
          </div>
          <h2 className="text-5xl md:text-8xl font-black uppercase tracking-tighter">
            PICK YOUR <span className="text-transparent" style={{ WebkitTextStroke: '2px #4f772d' }}>POISON</span>
          </h2>
        </div>

        <div className="grid md:grid-cols-2 gap-12 max-w-5xl mx-auto">
          
          {/* Rider Card */}
          <div className="bg-ridebid-green border-4 border-white p-8 md:p-12 flex flex-col brutal-shadow-white transform transition-transform hover:-translate-y-2 group">
            <div className="flex justify-between items-start mb-8">
              <h3 className="text-4xl md:text-5xl font-black text-black uppercase">Rider</h3>
              <span className="text-5xl">🚕</span>
            </div>
            <p className="font-mono text-black font-bold mb-10 flex-grow text-lg">
              &gt; SET YOUR OWN PRICE.<br/>
              &gt; NO SURGE PRICING BS.<br/>
              &gt; GET THERE FASTER.
            </p>
            <div className="flex flex-col gap-4">
              <button className="w-full bg-black text-white border-2 border-black font-mono font-bold text-xl py-4 uppercase brutal-shadow transition-all group-hover:bg-white group-hover:text-black">
                Sign Up as Rider
              </button>
              <button className="w-full bg-transparent text-black border-2 border-black font-mono font-bold py-3 uppercase hover:bg-black hover:text-white transition-colors">
                Login
              </button>
            </div>
          </div>

          {/* Driver Card */}
          <div className="bg-white border-4 border-ridebid-green p-8 md:p-12 flex flex-col brutal-shadow transform transition-transform hover:-translate-y-2 group">
            <div className="flex justify-between items-start mb-8">
              <h3 className="text-4xl md:text-5xl font-black text-black uppercase">Driver</h3>
              <span className="text-5xl">🏎️</span>
            </div>
            <p className="font-mono text-gray-700 font-bold mb-10 flex-grow text-lg">
              &gt; KEEP 100% OF THE BID.<br/>
              &gt; YOU ARE THE BOSS.<br/>
              &gt; EARN ON YOUR TERMS.
            </p>
            <div className="flex flex-col gap-4">
              <button className="w-full bg-ridebid-green text-black border-2 border-black font-mono font-bold text-xl py-4 uppercase brutal-shadow transition-all group-hover:bg-black group-hover:text-ridebid-green group-hover:border-ridebid-green">
                Sign Up as Driver
              </button>
              <button className="w-full bg-transparent text-black border-2 border-black font-mono font-bold py-3 uppercase hover:bg-black hover:text-white transition-colors">
                Login
              </button>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default CtaSection;
