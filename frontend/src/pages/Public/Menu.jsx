import React, { useEffect, useState } from "react";
import api from "../../api";

const Menu = () => {
  const [pages, setPages] = useState([]);
  const [activeTab, setActiveTab] = useState("kitchen");

  useEffect(() => {
    api.get("/menu").then((res) => setPages(res.data));
  }, []);

  return (
    <div className="bg-black min-h-screen pb-24">
      {/* Кнопки переключения */}
      <div className="flex p-4 gap-4">
        <button
          onClick={() => setActiveTab("kitchen")}
          className={`flex-1 py-3 rounded-2xl font-bold ${
            activeTab === "kitchen"
              ? "bg-orange-500 text-white"
              : "bg-slate-800 text-slate-400"
          }`}
        >
          КУХНЯ
        </button>
        <button
          onClick={() => setActiveTab("bar")}
          className={`flex-1 py-3 rounded-2xl font-bold ${
            activeTab === "bar"
              ? "bg-orange-500 text-white"
              : "bg-slate-800 text-slate-400"
          }`}
        >
          БАР
        </button>
      </div>

      <div className="px-4 space-y-4">
        {pages
          .filter((p) => p.category === activeTab)
          .sort((a, b) => a.order_num - b.order_num) // Сортируем по порядку
          .map((page) => (
            <img
              key={page.id}
              src={`${page.image_path}`}
              className="w-full rounded-3xl"
            />
          ))}
      </div>
    </div>
  );
};

export default Menu;
