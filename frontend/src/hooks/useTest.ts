import { useEffect, useState } from "react";
import type { Question, TestResult } from "../types";
import { getQuestions } from "../api/entities";
import { submitTest } from "../api/progress";

interface UseTest {
  questions: Question[];
  loading: boolean;
  answers: Record<string, number>;
  result: TestResult | null;
  answer: (questionId: string, optionIdx: number) => void;
  submit: () => Promise<TestResult>;
}

export function useTest(entityId: string, sessionId: string): UseTest {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<TestResult | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getQuestions(entityId).then((qs) => {
      if (active) {
        setQuestions(qs);
        setLoading(false);
      }
    });
    return () => {
      active = false;
    };
  }, [entityId]);

  const answer = (questionId: string, optionIdx: number) =>
    setAnswers((a) => ({ ...a, [questionId]: optionIdx }));

  const submit = async () => {
    const res = await submitTest({
      session_id: sessionId,
      entity_id: entityId,
      answers,
    });
    setResult(res);
    return res;
  };

  return { questions, loading, answers, result, answer, submit };
}
