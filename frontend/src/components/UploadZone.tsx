import { useRef, useState, useCallback } from "react";

interface Props {
  onFile: (file: File) => void;
  fileName?: string;
}

export default function UploadZone({ onFile, fileName }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("video/")) {
        onFile(file);
      }
    },
    [onFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFile(file);
  };

  return (
    <div
      className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 transition-colors cursor-pointer
        ${dragging ? "border-brand-500 bg-brand-900/20" : "border-gray-600 hover:border-brand-500 hover:bg-gray-800/40"}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="video/*"
        className="hidden"
        onChange={handleChange}
      />
      <div className="text-5xl mb-3">🏸</div>
      {fileName ? (
        <>
          <p className="text-brand-400 font-semibold text-lg">{fileName}</p>
          <p className="text-gray-400 text-sm mt-1">클릭하여 다른 파일 선택</p>
        </>
      ) : (
        <>
          <p className="text-gray-200 font-semibold text-lg">영상 파일을 드래그하거나 클릭하세요</p>
          <p className="text-gray-400 text-sm mt-1">MP4, MOV, AVI — 1080p/30fps 권장</p>
        </>
      )}
    </div>
  );
}
