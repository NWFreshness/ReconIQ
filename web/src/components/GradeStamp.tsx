export function gradeTone(grade: string): string {
  if (grade.startsWith("A")) return "text-success";
  if (grade.startsWith("B")) return "text-accent";
  if (grade.startsWith("C")) return "text-warn";
  return "text-danger";
}

export function GradeStamp({ grade, score, large }: { grade: string; score: number; large?: boolean }) {
  return (
    <span
      aria-label={`Prospect grade ${grade}, score ${score.toFixed(0)}`}
      className={`inline-flex flex-col items-center justify-center border-2 border-current font-display font-semibold leading-none ${gradeTone(grade)} ${
        large ? "w-28 h-28 -rotate-6 text-5xl outline outline-current outline-offset-4" : "w-11 h-11 text-lg"
      }`}
    >
      {grade}
      <span className={`font-sans font-medium tabular-nums ${large ? "text-sm mt-1.5" : "text-[10px] mt-0.5"}`}>
        {score.toFixed(0)}
      </span>
    </span>
  );
}
