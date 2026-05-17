import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";
import { Plus, Trash2, ArrowLeft, Image as ImageIcon } from "lucide-react";

const ManageMenu = () => {
  const [menuPages, setMenuPages] = useState([]);
  const navigate = useNavigate();

  const fetchMenu = async () => {
    try {
      const res = await api.get("/menu/");
      setMenuPages(res.data);
    } catch (err) {
      console.error("Ошибка загрузки страниц меню", err);
    }
  };

  useEffect(() => {
    fetchMenu();
  }, []);

  const handleDelete = async (id) => {
    if (window.confirm("Удалить этот лист меню?")) {
      try {
        await api.delete(`/menu/${id}`);
        setMenuPages(menuPages.filter((item) => item.id !== id));
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
        <h1 className="text-xl font-bold">Листы меню</h1>
        <button
          onClick={() => navigate("/admin/menu/new")}
          className="bg-orange-600 text-white p-2 rounded-xl shadow-lg"
        >
          <Plus size={20} />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {menuPages.map((page) => (
          <div
            key={page.id}
            className="relative bg-white p-2 rounded-2xl shadow-sm border border-slate-100"
          >
            <div className="aspect-[3/4] rounded-xl overflow-hidden bg-slate-100 mb-2">
              <img
                src={`${page.image_url}`}
                className="w-full h-full object-cover"
                alt=""
              />
            </div>
            <div className="flex items-center justify-between px-1">
              <span className="text-[10px] font-bold uppercase text-slate-400">
                {page.category === "kitchen" ? "Кухня" : "Бар"}
              </span>
              <button
                onClick={() => handleDelete(page.id)}
                className="text-rose-500 p-1"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ManageMenu;
