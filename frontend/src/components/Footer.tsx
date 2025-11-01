import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 py-16">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          <div>
            <Link to="/" className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">Magentix</span>
            </Link>
            <p className="text-gray-600 mb-4 max-w-md">
              Analyze your website for maximum performance with AI-powered insights. Evaluate SEO, conversion optimization, and technical performance.
            </p>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Product</h4>
            <ul className="space-y-2">
              <li><Link to="/features" className="text-gray-600 hover:text-blue-600 transition-colors">Features</Link></li>
              <li><Link to="/pricing" className="text-gray-600 hover:text-blue-600 transition-colors">Pricing</Link></li>
              <li><Link to="/about" className="text-gray-600 hover:text-blue-600 transition-colors">About</Link></li>
              <li><a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">API</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-200 pt-8">
          <div className="flex flex-col items-center justify-center text-center">
            <Link to="/" className="flex items-center space-x-2 mb-4">
              <div className="w-6 h-6 bg-gradient-to-r from-blue-600 to-blue-700 rounded-md flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold text-gray-900">Magentix</span>
            </Link>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>© 2024 Magnetix. All rights reserved.</span>
              <div className="flex items-center space-x-1">
                <span>Made with</span>
                <Heart className="w-4 h-4 text-red-500 fill-current" />
                <span>for better conversions</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}