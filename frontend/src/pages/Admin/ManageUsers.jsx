import React, { useEffect, useState } from "react";
import api from "../../api";
import {
  Trash2,
  ShieldCheck,
  User as UserIcon,
  ArrowLeft,
  Search,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const ManageUsers = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchUsers = async () => {
    try {
      const res = await api.get("/users");
      setUsers(res.data);
    } catch (err) {
      console.error("Ошибка загрузки пользователей", err);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const toggleAdmin = async (userId, currentRole) => {
    const newRole = currentRole === "ADMIN" ? "CLIENT" : "ADMIN";
    if (window.confirm(`Изменить роль пользователя на ${newRole}?`)) {
      try {
        await api.patch(`/users/${userId}/role`, { role: newRole });
        setUsers(
          users.map((u) => (u.id === userId ? { ...u, role: newRole } : u))
        );
      } catch (err) {
        alert("Ошибка при смене роли");
      }
    }
  };

  const deleteUser = async (userId) => {
    if (window.confirm("Удалить пользователя? Это действие нельзя отменить.")) {
      try {
        await api.delete(`/users/${userId}`);
        setUsers(users.filter((u) => u.id !== userId));
      } catch (err) {
        alert("Ошибка при удалении");
      }
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.tg_id?.toString().includes(searchTerm)
  );

  return (
    <div className="p-6 pb-24 bg-slate-50 min-h-screen">
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => navigate("/admin")}
          className="p-2 bg-white rounded-xl shadow-sm"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold text-slate-800">Пользователи</h1>
      </div>

      {/* Поиск */}
      <div className="relative mb-6">
        <Search
          className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
          size={18}
        />
        <input
          type="text"
          placeholder="Поиск по имени, username или ID..."
          className="w-full pl-12 pr-4 py-4 bg-white rounded-2xl border-none shadow-sm outline-none focus:ring-2 ring-indigo-500 transition-all"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="space-y-3">
        {filteredUsers.map((user) => (
          <div
            key={user.id}
            className="bg-white p-4 rounded-3xl flex items-center shadow-sm border border-slate-100"
          >
            {/* Аватар-заглушка */}
            <div
              className={`w-12 h-12 rounded-2xl flex items-center justify-center mr-4 ${
                user.role === "ADMIN"
                  ? "bg-indigo-100 text-indigo-600"
                  : "bg-slate-100 text-slate-400"
              }`}
            >
              {user.role === "ADMIN" ? (
                <ShieldCheck size={24} />
              ) : (
                <UserIcon size={24} />
              )}
            </div>

            {/* Данные юзера */}
            <div className="flex-1">
              <h3 className="font-bold text-slate-800 text-sm leading-tight">
                {user.first_name || "Без имени"}
                {user.username && (
                  <span className="text-indigo-500 font-medium ml-1">
                    @{user.username}
                  </span>
                )}
              </h3>
              <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-wider font-semibold">
                ID: {user.tg_id} • {user.role}
              </p>
            </div>

            {/* Кнопки действий */}
            <div className="flex gap-1">
              <button
                onClick={() => toggleAdmin(user.id, user.role)}
                title={
                  user.role === "ADMIN" ? "Разжаловать" : "Сделать админом"
                }
                className={`p-3 rounded-2xl transition-colors ${
                  user.role === "ADMIN"
                    ? "text-amber-500 bg-amber-50"
                    : "text-slate-400 bg-slate-50"
                }`}
              >
                <ShieldCheck size={20} />
              </button>
              <button
                onClick={() => deleteUser(user.id)}
                className="p-3 text-rose-500 bg-rose-50 rounded-2xl"
              >
                <Trash2 size={20} />
              </button>
            </div>
          </div>
        ))}

        {filteredUsers.length === 0 && (
          <div className="text-center py-20 text-slate-400">
            Пользователи не найдены
          </div>
        )}
      </div>
    </div>
  );
};

export default ManageUsers;
