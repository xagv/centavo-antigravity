import React from 'react';
import { Card } from '../ui/Card.jsx';

function formatCategory(category) {
  if (!category) return 'Sin categoría';
  return category.charAt(0).toUpperCase() + category.slice(1);
}

function formatAmount(amount) {
  const num = Number(amount);
  if (Number.isNaN(num)) return `$${amount}`;
  return `$${num.toLocaleString('es-CO')}`;
}

export function TransactionList({ transactions, isLoading, error }) {
  if (isLoading) {
    return (
      <Card>
        <div className="empty-state">
          <p>Cargando transacciones...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="empty-state">
          <p className="error-banner">{error}</p>
        </div>
      </Card>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <Card>
        <div className="empty-state">
          <span className="empty-state__icon" aria-hidden="true">
            💸
          </span>
          <h2 className="empty-state__title">No hay transacciones registradas</h2>
          <p>
            Aún no tienes ingresos ni gastos en este período. Cuando registres tu
            primer movimiento, aparecerá listado aquí.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <header>
        <h2 className="empty-state__title">Listado de transacciones</h2>
        <p className="brand-subtitle">Movimientos recientes categorizados</p>
      </header>
      <ul className="form-stack">
        {transactions.map((item) => (
          <li key={item.id} className="dashboard-header">
            <div>
              <strong className="empty-state__title">
                Categoría: {formatCategory(item.category)}
              </strong>
              <p className="brand-subtitle">Fecha: {item.date}</p>
            </div>
            <strong>{formatAmount(item.amount)}</strong>
          </li>
        ))}
      </ul>
    </Card>
  );
}
