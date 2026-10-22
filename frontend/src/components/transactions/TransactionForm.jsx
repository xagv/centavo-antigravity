import React from 'react';
import { Card } from '../ui/Card.jsx';
import { Input } from '../ui/Input.jsx';
import { Button } from '../ui/Button.jsx';

export function TransactionForm({
  amount,
  category,
  date,
  isSubmitting,
  error,
  onAmountChange,
  onCategoryChange,
  onDateChange,
  onSubmit,
}) {
  return (
    <Card>
      <header>
        <h2 className="empty-state__title">Registrar nuevo gasto</h2>
        <p className="brand-subtitle">
          Ingresa el monto, la categoría y la fecha de tu movimiento.
        </p>
      </header>

      <form className="form-stack" onSubmit={onSubmit}>
        <Input
          id="tx-amount"
          label="Monto ($)"
          type="text"
          value={amount}
          placeholder="50000"
          required
          onChange={onAmountChange}
        />

        <Input
          id="tx-category"
          label="Categoría"
          type="text"
          value={category}
          placeholder="Comida"
          required
          onChange={onCategoryChange}
        />

        <Input
          id="tx-date"
          label="Fecha"
          type="date"
          value={date}
          required
          onChange={onDateChange}
        />

        {error && <p className="error-banner">{error}</p>}

        <Button type="submit" variant="primary" disabled={isSubmitting}>
          {isSubmitting ? 'Registrando...' : 'Registrar gasto'}
        </Button>
      </form>
    </Card>
  );
}
