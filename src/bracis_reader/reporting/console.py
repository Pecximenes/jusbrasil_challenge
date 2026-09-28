"""Apresentação dos resultados da avaliação no terminal."""

from bracis_reader.evaluation.classification import ClassificationSummary
from bracis_reader.evaluation.evaluator import DocumentEvaluation, EvaluationSummary


class ConsoleReportPrinter:
    """Imprime uma tabela compacta com contagens e métricas."""

    _SEPARATOR = "-" * 46

    def print_report(
        self,
        evaluations: list[DocumentEvaluation],
        summary: EvaluationSummary,
        total_documents: int,
        n1_documents: int,
        n2_documents: int,
        criterion: str | None = None,
    ) -> None:
        if criterion:
            print(f"Critério de acerto: {criterion}")
        print(f"Total de documentos: {total_documents}")
        print(f"Documentos N1: {n1_documents}")
        print(f"Documentos N2: {n2_documents}\n")
        print(f"{'Documento':<16}{'Gold':>6}{'Pred':>6}{'TP':>6}{'FP':>6}{'FN':>6}")
        print(self._SEPARATOR)

        for item in evaluations:
            print(
                f"{item.documento_id:<16}"
                f"{item.expected:>6}"
                f"{item.predicted:>6}"
                f"{item.true_positives:>6}"
                f"{item.false_positives:>6}"
                f"{item.false_negatives:>6}"
            )

        print(self._SEPARATOR)
        print(
            f"{'TOTAL':<16}"
            f"{summary.expected:>6}"
            f"{summary.predicted:>6}"
            f"{summary.true_positives:>6}"
            f"{summary.false_positives:>6}"
            f"{summary.false_negatives:>6}"
        )
        print(f"\nPrecisão: {summary.precision:.4f}")
        print(f"Recall:   {summary.recall:.4f}")
        print(f"F1:       {summary.f1_score:.4f}")

    def print_classification(self, summary: ClassificationSummary) -> None:
        """Tabela de classificação por classe (nível 2 com peso 2)."""
        print("\nClassificação (IoU >= 0.5, classe + id; nível 2 com peso 2)")
        print(
            f"{'Classe':<12}{'TP':>8}{'FP':>8}{'FN':>8}{'Prec.':>8}{'Rec.':>8}{'F1':>8}"
        )
        print(self._SEPARATOR + "-" * 14)
        for item in summary.per_class:
            print(
                f"{item.classe:<12}"
                f"{item.true_positives:>8g}"
                f"{item.false_positives:>8g}"
                f"{item.false_negatives:>8g}"
                f"{item.precision:>8.4f}"
                f"{item.recall:>8.4f}"
                f"{item.f1_score:>8.4f}"
            )
        print(f"\nF1 macro:           {summary.macro_f1:.4f}")
        print(f"Tipo lei/juris:     {summary.tipo_corretos}/{summary.pares} corretos")
