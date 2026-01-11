import { useState } from "react";
import { generateQuiz } from "../api/quizApi";
import QuizCard from "./QuizCard";
import TakeQuiz from "./TakeQuiz";

export default function GenerateQuiz() {
  const [url, setUrl] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [quiz, setQuiz] = useState(null);
  const [mode, setMode] = useState("take"); 
  const [key, setKey] = useState(0);

  const handleGenerate = async () => {
    if (!url) {
      setError("Please enter a Wikipedia URL");
      return;
    }

    try {
      setError("");
      setLoading(true);

      // 🔁 RESET OLD STATE
      setQuiz(null);
      setMode("take");   
      setKey((prev) => prev + 1); 

      const data = await generateQuiz(url, numQuestions);
      setQuiz(data);

    } catch (err) {
      setError("Failed to generate quiz. Check backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="form">
        <input
          type="text"
          placeholder="Wikipedia URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        <input
          type="number"
          min="1"
          value={numQuestions}
          onChange={(e) => setNumQuestions(e.target.value)}
        />

        <button onClick={handleGenerate} disabled={loading}>
          {loading ? "Preparing a Test" : "Prepare Me"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {quiz && (
        <div>
          <div style={{ marginBottom: "15px" }}>
            <button onClick={() => setMode("view")}>View Answers</button>
            <button onClick={() => setMode("take")} style={{ marginLeft: "10px" }}>
              Take Quiz
            </button>
          </div>

          {mode === "view" &&
            quiz.questions.map((q) => (
              <QuizCard key={q.id} question={q} />
            ))}

          {/* 👇 THIS IS THE IMPORTANT FIX */}
          {mode === "take" && <TakeQuiz key={key} quiz={quiz} />}
        </div>
      )}
    </div>
  );
}
