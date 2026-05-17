import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";
import { Save, ArrowLeft, Upload } from "lucide-react";

const EditMenu = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [category, setCategory] = useState("kitchen");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return alert("Выберите файл!");

    const data = new FormData();
    data.append("file", file);
    data.append("category", category);

    try {
      await api.post("/menu/", data);
      navigate("/admin/menu");
    } catch (err) {
      alert("Ошибка загрузки");
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto">
      <div className="flex items-center mb-8">
        <button onClick={() => navigate(-1)} className="mr-4">
          <ArrowLeft />
        </button>
        <h1 className="text-xl font-bold">Загрузить лист</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="flex p-1 bg-slate-100 rounded-2xl">
          <button
            type="button"
            onClick={() => setCategory("kitchen")}
            className={`flex-1 py-3 rounded-xl text-sm font-bold transition ${
              category === "kitchen" ? "bg-white shadow-sm" : "text-slate-500"
            }`}
          >
            Кухня
          </button>
          <button
            type="button"
            onClick={() => setCategory("bar")}
            className={`flex-1 py-3 rounded-xl text-sm font-bold transition ${
              category === "bar" ? "bg-white shadow-sm" : "text-slate-500"
            }`}
          >
            Бар
          </button>
        </div>

        <div className="relative aspect-[3/4] bg-slate-100 rounded-3xl border-2 border-dashed border-slate-300 flex flex-col items-center justify-center overflow-hidden">
          {file ? (
            <img
              src={URL.createObjectURL(file)}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="text-slate-400 flex flex-col items-center">
              <Upload size={40} className="mb-2" />
              <span className="text-sm">Выбрать картинку</span>
            </div>
          )}
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            className="absolute inset-0 opacity-0"
          />
        </div>

        <button className="w-full bg-orange-600 text-white py-4 rounded-3xl font-bold shadow-lg">
          Добавить в меню
        </button>
      </form>
    </div>
  );
};

export default EditMenu;
