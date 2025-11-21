"use client";

import * as React from "react";

export interface DatePickerProps {
  selected?: Date;
  placeholder?: string;
  onSelect: (date: Date) => void;
}

export function DatePicker({
  selected,
  placeholder = "Choisir une date",
  onSelect,
}: DatePickerProps) {
  return (
    <input
      type="date"
      className="border rounded px-2 py-1"
      value={selected ? selected.toISOString().slice(0, 10) : ""}
      placeholder={placeholder}
      onChange={(e) => {
        const d = e.target.valueAsDate;
        if (d) onSelect(d);
      }}
    />
  );
}
