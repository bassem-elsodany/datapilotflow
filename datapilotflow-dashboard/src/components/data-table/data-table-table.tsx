import { DataTable, DataTableColumn, DataTableProps } from 'mantine-datatable';

/**
 * Thin wrapper around mantine-datatable's DataTable.
 * Automatically marks every column as resizable so users can drag column
 * borders left/right to adjust widths across the whole app.
 *
 * Note: this wrapper only supports the flat `columns` variant (not `groups`);
 * no caller currently uses `groups`, and mixing the two in the props type
 * defeats generic inference of `T` at call sites.
 */
export function DataTableTable<T>({
  columns,
  defaultColumnProps,
  ...rest
}: DataTableProps<T> & { columns: DataTableColumn<T>[] }) {
  const props = {
    ...rest,
    columns,
    defaultColumnProps: { resizable: true, ...defaultColumnProps },
  } as DataTableProps<T>;

  return <DataTable<T> {...props} />;
}
