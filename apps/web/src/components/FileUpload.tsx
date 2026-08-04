"use client";
import { useRef, useState } from "react";

export default function FileUpload({ onFile, disabled }: {
  onFile: (file: File, screenshots?: File[]) => void;
  disabled?: boolean;
}) {
  const [dragover, setDragover] = useState(false);
  const [selectedShots, setSelectedShots] = useState<File[]>([]);
  const docRef = useRef<HTMLInputElement>(null);
  const shotRef = useRef<HTMLInputElement>(null);
  const [docFile, setDocFile] = useState<File | null>(null);

  const handleDoc = (files: FileList | null) => {
    if (files && files.length > 0) {
      setDocFile(files[0]);
    }
  };

  const handleShots = (files: FileList | null) => {
    if (files) setSelectedShots(Array.from(files));
  };

  const submit = () => {
    if (docFile) onFile(docFile, selectedShots.length > 0 ? selectedShots : undefined);
  };

  return (
    <div>
      <div
        className={`dropzone${dragover ? " dragover" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
        onDragLeave={() => setDragover(false)}
        onDrop={(e) => { e.preventDefault(); setDragover(false); handleDoc(e.dataTransfer.files); }}
        onClick={() => !disabled && docRef.current?.click()}
      >
        <input
          ref={docRef} type="file" hidden
          accept=".txt,.md,.docx,.pdf"
          onChange={(e) => handleDoc(e.target.files)}
        />
        <p>Drag & drop your BA document here, or click to browse</p>
        <p className="muted">Supports .txt, .md, .docx, .pdf (max 10MB)</p>
      </div>
      {docFile && (
        <p className="muted" style={{ marginTop: "0.5rem" }}>Selected: {docFile.name}</p>
      )}
      <div style={{ marginTop: "0.75rem" }}>
        <label className="muted" style={{ marginRight: "0.5rem" }}>Screenshots (optional):</label>
        <input
          ref={shotRef} type="file" multiple
          accept="image/png,image/jpeg,image/webp"
          onChange={(e) => handleShots(e.target.files)}
          disabled={disabled}
        />
        {selectedShots.length > 0 && (
          <p className="muted" style={{ marginTop: "0.25rem" }}>
            {selectedShots.length} screenshot(s) selected
          </p>
        )}
      </div>
      <button
        disabled={disabled || !docFile}
        onClick={submit}
        style={{ marginTop: "0.75rem" }}
      >
        Generate Test Cases
      </button>
    </div>
  );
}
