interface Props {
  progress: number;
  step: string;
}

export default function ProgressBar({ progress, step }: Props) {
  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-gray-300">{step}</span>
        <span className="text-sm font-bold text-brand-400">{progress}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-brand-500 to-brand-400 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
