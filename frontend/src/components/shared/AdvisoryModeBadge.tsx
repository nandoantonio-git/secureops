/** Discreet indicator that blocking is not active -- informs, doesn't alarm. */
export function AdvisoryModeBadge() {
  return (
    <span
      className="advisory-badge"
      title="Modo consultivo: nenhum PR é bloqueado automaticamente ainda"
    >
      Modo consultivo
    </span>
  );
}
