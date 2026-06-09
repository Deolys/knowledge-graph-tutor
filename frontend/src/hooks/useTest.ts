import { useEffect, useState } from "react";
import type { Question, TestResult } from "../types";
import { getQuestions } from "../api/concepts";
import { submitTest } from "../api/progress";

interface UseTest {
  questions: Question[];
  loading: boolean;
  answers: Record<string, number>;
  result: TestResult | null;
  answer: (questionId: string, optionIdx: number) => void;
  submit: () => Promise<TestResult>;
}

/** Логика теста по понятию: загрузка вопросов, ответы, отправка. */
export function useTest(conceptId: string, sessionId: string): UseTest {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<TestResult | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getQuestions(conceptId).then((qs) => {
      if (active) {
        setQuestions(qs);
        setLoading(false);
      }
    });
    return () => {
      active = false;
    };
  }, [conceptId]);

  const answer = (questionId: string, optionIdx: number) =>
    setAnswers((a) => ({ ...a, [questionId]: optionIdx }));

  const submit = async () => {
    const res = await submitTest({
      session_id: sessionId,
      concept_id: conceptId,
      answers,
    });
    setResult(res);
    return res;
  };

  return { questions, loading, answers, result, answer, submit };
}
