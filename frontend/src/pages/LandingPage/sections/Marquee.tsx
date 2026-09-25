import React from 'react';

const Marquee: React.FC = () => {
  return (
    <div className="bg-ridebid-green text-black font-mono font-bold text-sm uppercase py-3 border-y-2 border-white overflow-hidden flex whitespace-nowrap">
      <div className="animate-[marquee_20s_linear_infinite] flex items-center shrink-0">
        <span className="mx-4">GET THAT RIDE</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">STOP WAITING</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">FIRST CLASS BOOKINGS</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">FIRE AND FORGET</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">GET THAT RIDE</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">STOP WAITING</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">FIRST CLASS BOOKINGS</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">FIRE AND FORGET</span>
        <span className="mx-4 text-white">///</span>
      </div>
      <div className="animate-[marquee_20s_linear_infinite] flex items-center shrink-0" aria-hidden="true">
        <span className="mx-4">GET THAT RIDE</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">STOP WAITING</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">FIRST CLASS BOOKINGS</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">FIRE AND FORGET</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">GET THAT RIDE</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">STOP WAITING</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">FIRST CLASS BOOKINGS</span>
        <span className="mx-4 text-white">///</span>
        <span className="mx-4">FIRE AND FORGET</span>
        <span className="mx-4 text-white">///</span>
      </div>
    </div>
  );
};

export default Marquee;
