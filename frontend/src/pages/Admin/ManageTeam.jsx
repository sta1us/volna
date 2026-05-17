import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";
import { UserPlus, Pencil, Trash2, ArrowLeft, User } from "lucide-react";

const ManageTeam = () => {
  const [team, setTeam] = useState([]);
  const navigate = useNavigate();

  // Загружаем список
  const fetchTeam = async () => {
    try {
      const res = await api.get("/team/");
      setTeam(res.data);
    } catch (err) {
      console.error("Ошибка загрузки команды", err);
    }
  };

  useEffect(() => {
    fetchTeam();
  }, []);

  const handleDelete = async (id) => {
    if (window.confirm("Удалить этого сотрудника?")) {
      try {
        await api.delete(`/team/${id}`);
        setTeam(team.filter((m) => m.id !== id)); // Обновляем список локально
      } catch (err) {
        alert("Ошибка при удалении");
      }
    }
  };

  return (
    <div className="p-6 pb-24 bg-slate-50 min-h-screen">
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={() => navigate("/admin")}
          className="p-2 bg-white rounded-xl shadow-sm"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold">Управление командой</h1>
        <button
          onClick={() => navigate("/admin/team/new")}
          className="bg-indigo-600 text-white p-2 rounded-xl shadow-lg"
        >
          <UserPlus size={20} />
        </button>
      </div>

      <div className="space-y-4">
        {team.map((member) => (
          <div
            key={member.id}
            className="bg-white p-4 rounded-3xl flex items-center shadow-sm border border-slate-100"
          >
            {/* Аватар */}
            <div className="w-16 h-16 rounded-2xl overflow-hidden bg-slate-100 mr-4">
              {member.image_url ? (
                <img
                  src={`${member.image_url}`}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-300">
                  <User />
                </div>
              )}
            </div>

            {/* Инфо */}
            <div className="flex-1">
              <h3 className="font-bold text-slate-800 leading-tight">
                {member.last_name} {member.first_name}
              </h3>
              <p className="text-xs text-slate-400">{member.role}</p>
            </div>

            {/* Действия */}
            <div className="flex gap-2">
              <button
                onClick={() => navigate(`/admin/team/edit/${member.id}`)}
                className="p-3 bg-slate-50 text-indigo-600 rounded-2xl active:bg-indigo-100"
              >
                <Pencil size={18} />
              </button>
              <button
                onClick={() => handleDelete(member.id)}
                className="p-3 bg-slate-50 text-rose-500 rounded-2xl active:bg-rose-100"
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
        ))}

        {team.length === 0 && (
          <div className="text-center py-20 text-slate-400 italic">
            В команде пока никого нет...
          </div>
        )}
      </div>
    </div>
  );
};

export default ManageTeam;
