import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import gsap from 'gsap';
import {
  Sparkles,
  Layers,
  Calendar,
  Shield,
  LogOut,
  KeyRound,
  User,
  ChevronDown,
  Menu,
  X,
} from 'lucide-react';
import { ChangePasswordModal } from './ChangePasswordModal';

// Formats display role name based on active user role: 'Admin' or 'Creator'
const formatDisplayName = (email?: string, isAdmin?: boolean): string => {
  if (isAdmin) return 'Admin';
  if (!email) return 'Creator';
  const prefix = email.split('@')[0].toLowerCase();
  if (prefix === 'admin') return 'Admin';
  if (prefix === 'creator') return 'Creator';
  return 'Creator';
};

export const Navbar: React.FC = () => {
  const { user, isAdmin, logout } = useAuth();
  const location = useLocation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);

  const userEmail = user?.email || '';
  const displayName = formatDisplayName(userEmail, isAdmin);

  // Close mobile drawer when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (navRef.current) {
      const links = navRef.current.querySelectorAll('.nav-item');
      if (links.length > 0) {
        gsap.fromTo(
          links,
          { opacity: 0, y: -6, scale: 0.95 },
          { opacity: 1, y: 0, scale: 1, duration: 0.35, stagger: 0.05, ease: 'back.out(1.4)' }
        );
      }
    }
  }, [isAdmin]);

  // Close user dropdown on outside click anywhere on the page
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [dropdownOpen]);

  // Strict role-based navigation: Creator sees Studio & Library; Admin sees all
  const navLinks = [
    { name: 'Studio', path: '/', icon: Sparkles },
    { name: 'Library', path: '/library', icon: Layers },
    ...(isAdmin ? [{ name: 'Schedules', path: '/schedules', icon: Calendar }] : []),
    ...(isAdmin ? [{ name: 'Admin Panel', path: '/admin', icon: Shield }] : []),
  ];

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 bg-white/95 backdrop-blur-md shadow-xs">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-3 sm:px-6 lg:px-8">
          {/* Official Brand Logo */}
          <Link to="/" className="flex items-center gap-2 sm:gap-3 group min-w-0">
            <div className="flex h-9 w-9 sm:h-10 sm:w-10 items-center justify-center p-0.5 group-hover:scale-105 transition-transform shrink-0">
              <img src="/42works_logo.png" alt="42 WORKS" className="h-full w-full object-contain" />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] sm:text-xs font-bold text-slate-800 tracking-tight truncate">
                AI Poster & Social Dispatch
              </p>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav ref={navRef} className="hidden md:flex items-center gap-1 rounded-2xl border border-slate-200 bg-slate-50/80 p-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`nav-item flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-white text-slate-900 shadow-sm border border-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-[#FFC20E]' : 'text-slate-400'}`} />
                  {link.name}
                </Link>
              );
            })}
          </nav>

          {/* Right Action Cluster: Account Pill + Mobile Menu Toggle */}
          <div className="flex items-center gap-2">
            {/* Professional Account Pill & Menu */}
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-1.5 sm:gap-2 rounded-full border border-slate-200 bg-white hover:bg-slate-50 px-2.5 sm:px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-2xs hover:border-slate-300 transition-all cursor-pointer"
                aria-label={`Account: ${displayName}`}
                title={displayName}
              >
                <div className="flex h-5 w-5 sm:h-6 sm:w-6 items-center justify-center rounded-full bg-slate-800 text-white shadow-xs">
                  <User className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                </div>
                <span className="font-bold text-slate-800 tracking-tight text-[11px] sm:text-xs">{displayName}</span>
                <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
              </button>

              {dropdownOpen && (
                <div className="absolute right-0 mt-2.5 w-72 rounded-2xl border border-slate-200/90 bg-white p-3 shadow-xl z-50 animate-in fade-in zoom-in-95 duration-150 text-slate-800">
                  {/* Profile Row */}
                  <div className="p-2 flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-full bg-slate-900 text-white shadow-xs shrink-0">
                      <User className="h-6 w-6" />
                    </div>

                    <div className="min-w-0 flex-1">
                      <h4 className="text-sm font-bold text-slate-900 truncate leading-snug">
                        {displayName}
                      </h4>
                      <p className="text-xs text-slate-500 truncate font-normal leading-snug">
                        {userEmail || (isAdmin ? 'admin@company.com' : 'creator@company.com')}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mt-2 pt-2 border-t border-slate-100 space-y-1">
                    <button
                      onClick={() => {
                        setDropdownOpen(false);
                        setChangePasswordOpen(true);
                      }}
                      className="flex w-full items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-xl transition-colors cursor-pointer"
                    >
                      <KeyRound className="h-4 w-4 text-slate-400" />
                      <span>Change Password</span>
                    </button>

                    <button
                      onClick={() => {
                        setDropdownOpen(false);
                        logout();
                      }}
                      className="flex w-full items-center gap-2.5 px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 rounded-xl transition-colors cursor-pointer"
                    >
                      <LogOut className="h-4 w-4 text-red-500" />
                      <span>Sign out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Mobile / Tablet Hamburger Button */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="flex md:hidden items-center justify-center h-9 w-9 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-colors cursor-pointer shadow-2xs"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white/98 backdrop-blur-lg px-4 py-3 shadow-lg animate-in slide-in-from-top-2 duration-150">
            <nav className="flex flex-col gap-1">
              {navLinks.map((link) => {
                const Icon = link.icon;
                const isActive = location.pathname === link.path;
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 rounded-xl px-4 py-3 text-xs font-bold transition-all ${
                      isActive
                        ? 'bg-amber-50 text-slate-950 border border-amber-200/80 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    }`}
                  >
                    <Icon className={`h-4 w-4 ${isActive ? 'text-amber-600' : 'text-slate-400'}`} />
                    <span>{link.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        )}
      </header>

      <ChangePasswordModal
        isOpen={changePasswordOpen}
        onClose={() => setChangePasswordOpen(false)}
      />
    </>
  );
};