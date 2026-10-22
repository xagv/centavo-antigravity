import { useState, useCallback } from 'react';
import { authService } from '../services/authService.js';

/**
 * Hook de estado de autenticación y formulario de inicio de sesión.
 * Mantiene el estado fuera del JSX de los componentes de vista.
 */
export function useAuth() {
  const [user, setUser] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleEmailChange = useCallback((event) => {
    setEmail(event.target.value);
  }, []);

  const handlePasswordChange = useCallback((event) => {
    setPassword(event.target.value);
  }, []);

  const handleLogin = useCallback(
    async (event) => {
      event.preventDefault();
      setIsLoading(true);
      setError(null);

      try {
        const session = await authService.login({ email, password });
        setUser(session.user);
      } catch (err) {
        setError(err.message || 'No fue posible iniciar sesión.');
      } finally {
        setIsLoading(false);
      }
    },
    [email, password]
  );

  const handleLogout = useCallback(async () => {
    await authService.logout();
    setUser(null);
    setPassword('');
  }, []);

  return {
    user,
    isAuthenticated: Boolean(user),
    email,
    password,
    isLoading,
    error,
    handleEmailChange,
    handlePasswordChange,
    handleLogin,
    handleLogout,
  };
}
