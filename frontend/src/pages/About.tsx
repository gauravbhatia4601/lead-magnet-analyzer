import React from 'react';
import { Users, Target, Award, TrendingUp, Heart } from 'lucide-react';

export default function About() {
  return (
    <div className="pt-24 pb-16">
      {/* Hero Section */}
      <section className="py-16 bg-gradient-to-br from-blue-50 via-white to-blue-50">
        <div className="container mx-auto px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              About <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-blue-700">Magnetix</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
              We're on a mission to help businesses optimize their lead generation and maximize conversions through intelligent analysis and actionable insights.
            </p>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-4xl font-bold text-gray-900 mb-6">Our Mission</h2>
                <p className="text-lg text-gray-600 mb-6 leading-relaxed">
                  At Magnetix, we believe that every business deserves to maximize their lead generation potential. Too many companies struggle with poor conversion rates simply because they don't know what's holding them back.
                </p>
                <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                  Our AI-powered platform analyzes websites across multiple dimensions to identify optimization opportunities that can dramatically improve conversion rates and lead quality.
                </p>
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <Target className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Data-Driven Optimization</h3>
                    <p className="text-gray-600">Every recommendation is backed by proven conversion principles</p>
                  </div>
                </div>
              </div>
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-8 rounded-2xl">
                <div className="grid grid-cols-2 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600 mb-2">10,000+</div>
                    <div className="text-sm text-gray-600">Websites Analyzed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600 mb-2">35%</div>
                    <div className="text-sm text-gray-600">Avg. Conversion Increase</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600 mb-2">2.5M+</div>
                    <div className="text-sm text-gray-600">Leads Generated</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600 mb-2">98%</div>
                    <div className="text-sm text-gray-600">Customer Satisfaction</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Our Values</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              The principles that guide everything we do at Magnetix.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <div className="text-center p-8 bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow">
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Results-Focused</h3>
              <p className="text-gray-600">
                We measure our success by the tangible improvements our customers achieve in their conversion rates and lead quality.
              </p>
            </div>

            <div className="text-center p-8 bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow">
              <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Users className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Customer-Centric</h3>
              <p className="text-gray-600">
                Every feature we build and every recommendation we make is designed with our customers' success in mind.
              </p>
            </div>

            <div className="text-center p-8 bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow">
              <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Award className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Excellence</h3>
              <p className="text-gray-600">
                We continuously improve our algorithms and analysis to provide the most accurate and actionable insights possible.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Meet Our Team</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              The experts behind Magnetix's powerful lead generation optimization platform.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <div className="text-center">
              <div className="w-32 h-32 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white text-4xl font-bold mx-auto mb-6">
                A
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Alex Thompson</h3>
              <p className="text-blue-600 font-medium mb-4">CEO & Co-Founder</p>
              <p className="text-gray-600">
                Former VP of Growth at two unicorn startups. Expert in conversion optimization with 10+ years of experience.
              </p>
            </div>

            <div className="text-center">
              <div className="w-32 h-32 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center text-white text-4xl font-bold mx-auto mb-6">
                S
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Sarah Kim</h3>
              <p className="text-blue-600 font-medium mb-4">CTO & Co-Founder</p>
              <p className="text-gray-600">
                AI/ML engineer with expertise in web analytics and automated optimization. Previously at Google and Meta.
              </p>
            </div>

            <div className="text-center">
              <div className="w-32 h-32 bg-gradient-to-br from-purple-400 to-purple-600 rounded-full flex items-center justify-center text-white text-4xl font-bold mx-auto mb-6">
                M
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Marcus Rodriguez</h3>
              <p className="text-blue-600 font-medium mb-4">Head of Product</p>
              <p className="text-gray-600">
                Product strategist focused on user experience and conversion psychology. 8+ years in growth product roles.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Story Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">Our Story</h2>
              <p className="text-xl text-gray-600">
                How Magnetix came to be and where we're headed.
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-sm">
              <div className="prose prose-lg max-w-none text-gray-600">
                <p className="mb-6">
                  Magnetix was born out of frustration. As growth marketers at various startups, our founders repeatedly encountered the same problem: businesses were leaving money on the table because they didn't know how to optimize their lead generation effectively.
                </p>
                <p className="mb-6">
                  Traditional conversion rate optimization was either too expensive (requiring dedicated agencies) or too time-consuming (manual audits taking weeks). Meanwhile, businesses were losing potential customers every day due to poorly optimized lead magnets, confusing value propositions, and subpar user experiences.
                </p>
                <p className="mb-6">
                  We realized that AI could democratize access to expert-level conversion optimization insights. By analyzing thousands of high-converting websites and identifying the patterns that drive results, we could provide instant, actionable recommendations to any business.
                </p>
                <p>
                  Today, Magnetix has helped over 10,000 websites improve their lead generation, resulting in millions of additional leads and hundreds of millions in additional revenue for our customers. We're just getting started.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-blue-700">
        <div className="container mx-auto px-6 text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Heart className="w-6 h-6 text-red-400 fill-current" />
            <span className="text-blue-100">Made with love for better conversions</span>
          </div>
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to Join Our Success Stories?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Let us help you optimize your lead generation and achieve the growth you deserve.
          </p>
          <button className="bg-white text-blue-600 px-8 py-4 rounded-2xl font-semibold text-lg hover:bg-gray-100 transition-colors">
            Start Your Free Analysis
          </button>
        </div>
      </section>
    </div>
  );
}