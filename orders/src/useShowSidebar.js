import { useLocation } from 'react-router-dom';

export const useShowSidebar = () => {
  const location = useLocation();
  return location.pathname !== "/Cloud_Project/";
};