import React from 'react';
import { Button } from '../ui/Button.jsx';
import { TransactionForm } from '../transactions/TransactionForm.jsx';
import { TransactionList } from '../transactions/TransactionList.jsx';

export function DashboardView({
  user,
  transactions,
  isLoadingTransactions,
  transactionsError,
  amount,
  category,
  date,
  isSubmittingTransaction,
  submitTransactionError,
  onAmountChange,
  onCategoryChange,
  onDateChange,
  onCreateTransaction,
  onLogout,
}) {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div>
          <h1 className="brand-title">Centavo 💰</h1>
          <p className="brand-subtitle">
            Hola, {user?.name || user?.email} — Panel principal de transacciones
          </p>
        </div>
        <Button variant="secondary" onClick={onLogout}>
          Cerrar sesión
        </Button>
      </header>

      <main className="form-stack">
        <TransactionForm
          amount={amount}
          category={category}
          date={date}
          isSubmitting={isSubmittingTransaction}
          error={submitTransactionError}
          onAmountChange={onAmountChange}
          onCategoryChange={onCategoryChange}
          onDateChange={onDateChange}
          onSubmit={onCreateTransaction}
        />

        <TransactionList
          transactions={transactions}
          isLoading={isLoadingTransactions}
          error={transactionsError}
        />
      </main>
    </div>
  );
}
