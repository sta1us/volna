import React from "react";
import { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import api from "./api"; // axios экземпляр

import ScrollToTop from "./components/ScrollToTop";

// Импортируем страницы
// Публичные
import Events from "./pages/Public/Events";
import EventDetail from "./pages/Public/EventDetail";
import Menu from "./pages/Public/Menu";
import Team from "./pages/Public/Team";
import Contacts from "./pages/Public/Contacts";
import Reviews from "./pages/Public/Reviews";
import Suggestions from "./pages/Public/Suggestions";
import Home from "./pages/Public/Home";
import Login from "./pages/Public/Login";

// Admin
import AdminDashboard from "./pages/Admin/AdminDashboard";
import ManageEvents from "./pages/Admin/ManageEvents";
import ManageEventsMedia from "./pages/Admin/ManageEventsMedia";
import EditEvents from "./pages/Admin/EditEvents";
import ManageTeam from "./pages/Admin/ManageTeam";
import EditTeam from "./pages/Admin/EditTeam";
import ManageMenu from "./pages/Admin/ManageMenu";
import EditMenu from "./pages/Admin/EditMenu";
import EditLocation from "./pages/Admin/EditLocation";
import ManageReviews from "./pages/Admin/ManageReviews";
import ManageUsers from "./pages/Admin/ManageUsers";
import ManageSuggestions from "./pages/Admin/ManageSuggestions";
import ManageMedia from "./pages/Admin/ManageMedia";
import MediaUpload from "./pages/Admin/MediaUpload";
import AdminStats from "./pages/Admin/Stats";

// Компонент-обертка для защиты админки
const AdminRoute = ({ children }) => {
  const [isAdmin, setIsAdmin] = useState(null); // null - пока идет проверка

  useEffect(() => {
    const token = localStorage.getItem("token");
    // Если токена нет совсем, мы даже не пытаемся стучаться на бэкенд
    if (!token) {
      setIsAdmin(false);
      return;
    }

    const checkAdmin = async () => {
      console.log("Отправляю запрос на проверку админа..."); // Лог во фронтенд-консоли
      try {
        // Делаем реальный запрос к бэкенду
        const response = await api.get("/auth/verify-admin");

        if (response.data.is_admin) {
          setIsAdmin(true);
        } else {
          setIsAdmin(false);
        }
      } catch (err) {
        setIsAdmin(false);
      }
    };
    checkAdmin();
  }, []);

  if (isAdmin === null) return <div>Загрузка...</div>; // Или пустой экран

  return isAdmin ? children : <Navigate to="/" replace />;
};

function App() {
  return (
    <Router>
      <ScrollToTop />
      <div className="pb-16">
        {" "}
        {/* Отступ снизу, чтобы контент не перекрывался баром */}
        <div className="antialiased text-slate-900">
          <Routes>
            {/* Публичные маршруты */}
            <Route path="/" element={<Home />} />
            <Route path="/events" element={<Events />} />
            <Route path="/events/:id" element={<EventDetail />} />
            <Route path="/menu" element={<Menu />} />
            <Route path="/team" element={<Team />} />
            <Route path="/contacts" element={<Contacts />} />
            <Route path="/reviews" element={<Reviews />} />
            <Route path="/suggestions" element={<Suggestions />} />
            <Route path="/login" element={<Login />} />

            {/* Защищенные маршруты админки */}
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminDashboard />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/location"
              element={
                <AdminRoute>
                  <EditLocation />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/reviews"
              element={
                <AdminRoute>
                  <ManageReviews />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/suggestions"
              element={
                <AdminRoute>
                  <ManageSuggestions />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/team"
              element={
                <AdminRoute>
                  <ManageTeam />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/team/new"
              element={
                <AdminRoute>
                  <EditTeam />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/team/edit/:id"
              element={
                <AdminRoute>
                  <EditTeam />
                </AdminRoute>
              }
            />

            <Route
              path="/admin/events"
              element={
                <AdminRoute>
                  <ManageEvents />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/events/new"
              element={
                <AdminRoute>
                  <EditEvents />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/events/edit/:id"
              element={
                <AdminRoute>
                  <EditEvents />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/events/media/:id"
              element={
                <AdminRoute>
                  <ManageEventsMedia />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/events/media/upload/:id"
              element={
                <AdminRoute>
                  <MediaUpload />
                </AdminRoute>
              }
            />

            <Route
              path="/admin/menu"
              element={
                <AdminRoute>
                  <ManageMenu />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/menu/new"
              element={
                <AdminRoute>
                  <EditMenu />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/menu/edit/:id"
              element={
                <AdminRoute>
                  <EditMenu />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <AdminRoute>
                  <ManageUsers />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/stats"
              element={
                <AdminRoute>
                  <AdminStats />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/media/upload"
              element={
                <AdminRoute>
                  <MediaUpload />
                </AdminRoute>
              }
            />
            <Route
              path="/admin/media"
              element={
                <AdminRoute>
                  <ManageMedia />
                </AdminRoute>
              }
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
