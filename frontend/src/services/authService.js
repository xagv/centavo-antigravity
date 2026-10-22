import { requestService, setAuthToken } from './apiClient.js';

/**
 * Capa de servicio para autenticación contra `auth-service`.
 */
export const authService = {
  async login({ email, password }) {
    if (!email || !password) {
      throw new Error('Ingresa tu correo y contraseña para continuar.');
    }

    let tokenData;
    try {
      tokenData = await requestService('auth', '/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
    } catch {
      await requestService('auth', '/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      tokenData = await requestService('auth', '/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
    }

    setAuthToken(tokenData.access_token);

    const sessionUser = await requestService('auth', '/auth/session', {
      method: 'GET',
    });

    return {
      user: {
        id: sessionUser.id,
        email: sessionUser.email,
        name: sessionUser.email.split('@')[0],
      },
      token: tokenData.access_token,
    };
  },

  async logout() {
    setAuthToken(null);
  },
};
