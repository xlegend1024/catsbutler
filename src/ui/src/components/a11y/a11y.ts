export function withAriaLabel(label: string): { "aria-label": string } {
  return { "aria-label": label };
}

export function focusById(id: string): void {
  const element = document.getElementById(id);
  if (element) {
    element.focus();
  }
}
