import React from 'react';
import { Card } from '../ui/Card.jsx';
import { Input } from '../ui/Input.jsx';
import { Button } from '../ui/Button.jsx';

export function LoginView({
  email,
  password,
  isLoading,
  error,
  onEmailChange,
  onPasswordChange,
  onSubmit,
}) {
  return (
    <main className="layout-centered">
      <Card className="login-card">
        <header>
          <h1 className="brand-title">Centavo 💰</h1>
          <p className="brand-subtitle">
            Inicia sesión para gestionar tus gastos y presupuestos.
          </p>
        </header>

        <form className="form-stack" onSubmit={onSubmit}>
          <Input
            id="login-email"
            label="Correo electrónico"
            type="email"
            value={email}
            placeholder="tu@correo.com"
            required
            onChange={onEmailChange}
          />

          <Input
            id="login-password"
            label="Contraseña"
            type="password"
            value={password}
            placeholder="••••••••"
            required
            onChange={onPasswordChange}
          />

          {error && <p className="error-banner">{error}</p>}

          <Button type="submit" variant="primary" disabled={isLoading}>
            {isLoading ? 'Ingresando...' : 'Iniciar sesión'}
          </Button>
        </form>
      </Card>
    </main>
  );
}
