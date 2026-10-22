import React from 'react';

export function Button({
  children,
  type = 'button',
  variant = 'primary',
  disabled = false,
  onClick,
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`ui-button ui-button--${variant}`}
    >
      {children}
    </button>
  );
}
