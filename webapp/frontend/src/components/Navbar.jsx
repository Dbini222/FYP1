// components/Navbar.js

import React from 'react';
import Image from 'next/image';

const Navbar = () => {
  return (
    <nav className="flex justify-between items-center p-4 bg-white shadow-md">
      <div className="flex items-center">
        <Image
          src="/logo.svg" // Update to your logo path
          alt="Logo"
          width={128}
          height={32}
        />
      </div>
      <ul className="hidden md:flex space-x-8">
        <li>
          <a href="#services" className="text-gray-600 hover:text-black">
            Form an LLC
          </a>
        </li>
        <li>
          <a href="#services" className="text-gray-600 hover:text-black">
            Services
          </a>
        </li>
        <li>
          <a href="#resources" className="text-gray-600 hover:text-black">
            Resources
          </a>
        </li>
        <li>
          <a href="#about" className="text-gray-600 hover:text-black">
            Why Tailor Brands?
          </a>
        </li>
      </ul>
      <ul className="flex space-x-4">
        <li>
          <a href="#contact" className="text-gray-600 hover:text-black">
            Contact us
          </a>
        </li>
        <li>
          <a href="#login" className="text-gray-600 hover:text-black">
            Log in
          </a>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
