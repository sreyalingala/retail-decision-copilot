"use client";

import * as React from "react";

export function ResultTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: unknown[][];
}) {
  return (
    <div className="overflow-hidden rounded-lg border">
      <div className="max-h-[420px] overflow-auto">
        <table className="min-w-full border-collapse">
          <thead className="sticky top-0 bg-background">
            <tr>
              {columns.map((c) => (
                <th
                  key={c}
                  className="border-b bg-background px-3 py-2 text-left text-xs font-medium text-muted-foreground"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td className="px-3 py-6 text-sm text-muted-foreground" colSpan={Math.max(columns.length, 1)}>
                  No rows returned.
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-muted/30">
                  {columns.map((c, colIdx) => (
                    <td key={c} className="border-b px-3 py-2 text-sm">
                      {String(row[colIdx] ?? "")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

