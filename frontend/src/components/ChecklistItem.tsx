import type { ReactNode } from "react";

interface ChecklistItemProps {
  checked: boolean;
  disabled: boolean;
  onToggle: () => void;
  children: ReactNode;
}

/** One checkbox row. The whole row is the label, so the click and touch target is large. */
export default function ChecklistItem({ checked, disabled, onToggle, children }: ChecklistItemProps) {
  return (
    <li>
      <label>
        <input type="checkbox" checked={checked} disabled={disabled} onChange={onToggle} />
        <span>{children}</span>
      </label>
    </li>
  );
}
