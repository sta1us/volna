import { jwtDecode } from "jwt-decode";

export const getRoleFromToken = () => {
  const token = localStorage.getItem("token");
  if (!token) return null;

  try {
    const decoded = jwtDecode(token);
    // Обычно роль в FastAPI/Jose зашита в поле "sub" или отдельное поле "role" (проверить, как упакован токен на бекенде)
    return decoded.role || null;
  } catch (error) {
    console.error("Invalid token");
    return null;
  }
};

export const isAdmin = () => {
  return getRoleFromToken() === "ADMIN";
};
