"use client";

import { useState } from "react";
import { queryAIAssistant, AIMessage, AIQueryResult } from "@/lib/ai-assistant";

/**
 * Hook to interact with the AI assistant
 */
export function useAIAssistant() {
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Send a question to the AI
   */
  const askQuestion = async (question: string) => {
    if (!question.trim()) return;

    // Add user message
    const userMessage: AIMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    
    setIsLoading(true);
    setError(null);

    try {
      // Query the AI with conversation history
      const result = await queryAIAssistant(question, messages);

      // Add AI response
      const assistantMessage: AIMessage = {
        role: "assistant",
        content: result.answer,
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
      
      return result;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to get response";
      setError(errorMsg);
      
      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Clear conversation history
   */
  const clearHistory = () => {
    setMessages([]);
    setError(null);
  };

  return {
    messages,
    isLoading,
    error,
    askQuestion,
    clearHistory,
  };
}

