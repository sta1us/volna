import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api";
import { Camera, Save, ArrowLeft } from "lucide-react";

const EditTeam = () => {
  const { id } = useParams(); // Если id есть, значит мы в режиме редактирования
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    middle_name: "",
    role: "",
    description: "",
    order_priority: "",
  });

  useEffect(() => {
    if (id) {
      api.get(`/team/${id}`).then((res) => setFormData(res.data));
    }
  }, [id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = new FormData();
    data.append("first_name", formData.first_name);
    data.append("last_name", formData.last_name);
    data.append("middle_name", formData.middle_name);
    data.append("description", formData.description);
    data.append("role", formData.role);
    data.append("order_priority", formData.order_priority);
    if (file) data.append("file", file);

    try {
      if (id) {
        await api.put(`/team/${id}`, data); // Метод PUT для обновления
      } else {
        await api.post("/team/", data); // Метод POST для создания
      }
      navigate("/admin/team");
    } catch (err) {
      alert("Ошибка сохранения");
    }
  };

  return (
    <div className="p-6 pb-24 max-w-md mx-auto">
      <div className="flex items-center mb-8">
        <button onClick={() => navigate(-1)} className="mr-4">
          <ArrowLeft />
        </button>
        <h1 className="text-xl font-bold">
          {id ? "Редактировать" : "Добавить"} профиль
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="relative w-32 h-32 mx-auto bg-slate-200 rounded-full overflow-hidden border-4 border-white shadow-md">
          {file ? (
            <img
              src={URL.createObjectURL(file)}
              className="w-full h-full object-cover"
            />
          ) : formData.image_url ? (
            <img
              src={`${formData.image_url}`}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400">
              <Camera />
            </div>
          )}
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            className="absolute inset-0 opacity-0 cursor-pointer"
          />
        </div>

        <input
          type="text"
          placeholder="Фамилия"
          value={formData.last_name}
          className="w-full p-4 bg-white rounded-2xl border"
          onChange={(e) =>
            setFormData({ ...formData, last_name: e.target.value })
          }
        />
        <input
          type="text"
          placeholder="Имя"
          value={formData.first_name}
          className="w-full p-4 bg-white rounded-2xl border"
          onChange={(e) =>
            setFormData({ ...formData, first_name: e.target.value })
          }
        />
        <input
          type="text"
          placeholder="Отчество"
          value={formData.middle_name}
          className="w-full p-4 bg-white rounded-2xl border"
          onChange={(e) =>
            setFormData({ ...formData, middle_name: e.target.value })
          }
        />
        <input
          type="number"
          placeholder="Приоритет"
          value={formData.order_priority}
          className="w-full p-4 bg-white rounded-2xl border"
          onChange={(e) =>
            setFormData({ ...formData, order_priority: e.target.value })
          }
        />
        <textarea
          placeholder="Биография сотрудника"
          value={formData.description}
          className="w-full p-4 bg-white rounded-2xl border h-32"
          onChange={(e) =>
            setFormData({ ...formData, description: e.target.value })
          }
        />
        <input
          type="text"
          placeholder="Роль"
          value={formData.role}
          className="w-full p-4 bg-white rounded-2xl shadow-sm border outline-none"
          onChange={(e) => setFormData({ ...formData, role: e.target.value })}
        />

        <button className="w-full bg-indigo-600 text-white py-4 rounded-3xl font-bold shadow-lg flex items-center justify-center gap-2">
          <Save size={20} /> Сохранить
        </button>
      </form>
    </div>
  );
};

export default EditTeam;
