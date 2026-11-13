import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { SparkyMascot } from './components/SparkyMascot';
import { LoginPage } from './views/LoginPage';
import { StudioPage } from './views/StudioPage';
import { LibraryPage } from './views/LibraryPage';
import { SchedulesPage } from './views/SchedulesPage';
import { AdminPage } from './views/AdminPage';

const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col selection:bg-[#FFC20E]/30 selection:text-slate-900">
      <Navbar />
      <main className="flex-1 bg-white">{children}</main>
      <SparkyMascot />
      <Footer />
    </div>
  );
};

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAdmin } = useAuth();
  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedLayout>
                <StudioPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/library"
            element={
              <ProtectedLayout>
                <LibraryPage />
              </ProtectedLayout>
            }
          />
          <Route
            path="/schedules"
            element={
              <ProtectedLayout>
                <AdminRoute>
                  <SchedulesPage />
                </AdminRoute>
              </ProtectedLayout>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedLayout>
                <AdminRoute>
                  <AdminPage />
                </AdminRoute>
              </ProtectedLayout>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
