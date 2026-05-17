'use client';

import { GitCompare, TrendingDown, LineChart, HelpCircle } from 'lucide-react';

const PROMPTS = [
  { text: 'Compare Meta and Google', icon: GitCompare },
  { text: 'Why is Netflix declining?', icon: TrendingDown },
  { text: 'What is Tesla trading at?', icon: LineChart },
  { text: 'Should I buy NVIDIA?', icon: HelpCircle },
];

interface SuggestedPromptsProps {
  onSelect: (text: string) => void;
  disabled?: boolean;
}

export function SuggestedPrompts({ onSelect, disabled }: SuggestedPromptsProps) {
  return (
    <div className="suggested-prompts">
      <p className="suggested-label">Suggestions</p>
      <div className="prompt-grid">
        {PROMPTS.map((p) => (
          <button
            key={p.text}
            type="button"
            className="prompt-chip"
            disabled={disabled}
            onClick={() => onSelect(p.text)}
          >
            <p.icon size={15} />
            {p.text}
          </button>
        ))}
      </div>
    </div>
  );
}
