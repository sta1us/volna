import React, { useEffect, useState } from "react";
import api from "../../api";
import { Instagram, Send } from "lucide-react";

const Team = () => {
  const [team, setTeam] = useState([]);

  useEffect(() => {
    // Загружаем список сотрудников с бэкенда
    api
      .get("/team/")
      .then((res) => setTeam(res.data))
      .catch((err) => console.error("Ошибка загрузки команды", err));
  }, []);

  return (
    <div className="p-6 pb-24 bg-slate-50 min-h-screen">
      <h1 className="text-4xl font-black mb-8 text-slate-900">Команда</h1>

      <div className="grid grid-cols-2 gap-4">
        {team.map((member) => (
          <div
            key={member.id}
            className="bg-white rounded-3xl overflow-hidden shadow-sm border border-slate-100"
          >
            <div className="h-48 overflow-hidden">
              <img
                src={`${member.image_url}`}
                alt={member.name}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="p-4">
              <h3 className="font-bold text-lg leading-tight">
                {member.last_name} {member.first_name}
              </h3>
              <p className="text-indigo-600 text-xs font-medium uppercase mt-1">
                {member.role}
              </p>

              <div className="flex gap-3 mt-3 text-slate-400">
                {member.instagram && <Instagram size={18} />}
                {member.telegram && <Send size={18} />}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Team;
