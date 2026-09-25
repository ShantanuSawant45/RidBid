import React from 'react';
import Navbar from './sections/Navbar';
import HeroSection from './sections/HeroSection';
import Marquee from './sections/Marquee';
import FeatureInfo from './sections/FeatureInfo';
import CtaSection from './sections/CtaSection';

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-ridebid-black font-sans text-white selection:bg-ridebid-green selection:text-black">
      <Navbar />
      <main>
        <HeroSection />
        <Marquee />
        <FeatureInfo />
        <CtaSection />
      </main>
    </div>
  );
};

export default LandingPage;
