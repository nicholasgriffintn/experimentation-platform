/**
 * Formats a date string to ISO format with timezone
 * @param dateStr The date string to format
 * @returns The formatted date string in ISO format with timezone
 */
export function formatDateToISO(dateStr: string): string {
  if (!dateStr) return "";
  return `${dateStr}:00Z`;
}
