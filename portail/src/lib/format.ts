/**
 * Formate un montant en Ariary : entier, séparateur d'espace, suffixe " Ar".
 * Ex. 12500 -> "12 500 Ar". Pas de décimales (l'Ariary s'utilise en entiers).
 */
export function formatAriary(amount: number): string {
  const rounded = Math.round(amount);
  const grouped = Math.abs(rounded)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const sign = rounded < 0 ? "-" : "";
  return `${sign}${grouped} Ar`;
}
