import React from 'react';

export function Input({
  id,
  label,
  type = 'text',
  value,
  placeholder,
  required = false,
  onChange,
}) {
  return (
    <div className="ui-field">
      {label && (
        <label htmlFor={id} className="ui-label">
          {label}
        </label>
      )}
      <input
        id={id}
        type={type}
        value={value}
        placeholder={placeholder}
        required={required}
        onChange={onChange}
        className="ui-input"
      />
    </div>
  );
}
