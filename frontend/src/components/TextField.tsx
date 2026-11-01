import type { InputHTMLAttributes } from "react";

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "id" | "name"> {
  name: string;
  label: string;
  value: string;
  error?: string;
  onChange: (name: string, value: string) => void;
}

/** A labelled input whose error message is linked to it for screen readers. */
export default function TextField({ name, label, value, error, onChange, ...inputProps }: TextFieldProps) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <input
        {...inputProps}
        id={name}
        name={name}
        value={value}
        onChange={(event) => onChange(name, event.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${name}-error` : undefined}
      />
      {error && (
        <span className="err" id={`${name}-error`}>
          {error}
        </span>
      )}
    </div>
  );
}
