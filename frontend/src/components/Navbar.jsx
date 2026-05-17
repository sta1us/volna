import { Link } from "react-router-dom";
import { User, Calendar, Utensils } from "lucide-react";

const Navbar = () => {
  const token = localStorage.getItem("token");

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t flex justify-around p-3 pb-6 shadow-lg z-50">
      <Link to="/" className="flex flex-col items-center text-slate-600">
        <Calendar size={24} />
        <span className="text-[10px] mt-1">Афиша</span>
      </Link>

      <Link to="/menu" className="flex flex-col items-center text-slate-600">
        <Utensils size={24} />
        <span className="text-[10px] mt-1">Меню</span>
      </Link>

      {/* Если токена нет — показываем вход, если есть — иконку профиля */}
      <Link
        to={token ? "/admin" : "/login"}
        className="flex flex-col items-center text-indigo-600 font-bold"
      >
        <User size={24} />
        <span className="text-[10px] mt-1">{token ? "Админ" : "Войти"}</span>
      </Link>
    </nav>
  );
};

export default Navbar;
