export const money = (value: number | string | undefined) =>
  new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(Number(value || 0));

export const normalizeStatus = (value: string) =>
  value.toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '').replaceAll('_', '-');

export function paymentBalance(total: number, payments: number[]) {
  const paid = payments.reduce((sum, amount) => sum + amount, 0);
  return { paid: Number(paid.toFixed(2)), remaining: Number(Math.max(0, total - paid).toFixed(2)), closed: Math.abs(total - paid) < 0.005 };
}
