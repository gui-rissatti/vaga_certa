
import React, { useState, useEffect } from 'react';
import type { UserInput } from '../types';
import { UploadIcon, FileIcon, StopIcon } from './Icons';
import * as pdfjsLib from 'pdfjs-dist';

// Set worker path for pdf.js
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString();

interface InputSectionProps {
  userInput: UserInput;
  onInputChange: (newInput: Partial<UserInput>) => void;
  onGenerate: () => void;
  onStop: () => void;
  isGenerating: boolean;
  useThinkingMode: boolean;
  setUseThinkingMode: (value: boolean) => void;
}

const Label: React.FC<{ htmlFor: string; children: React.ReactNode }> = ({ htmlFor, children }) => (
  <label htmlFor={htmlFor} className="block text-sm font-medium text-content-200 mb-2">
    {children}
  </label>
);

const TextInput: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = (props) => (
    <input
      {...props}
      className="w-full p-3 bg-base-200 border border-base-300 rounded-md focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition-shadow"
    />
);

const TextArea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement>> = (props) => (
  <textarea
    {...props}
    className="w-full p-3 bg-base-200 border border-base-300 rounded-md focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition-shadow resize-y"
  />
);

const Select: React.FC<React.SelectHTMLAttributes<HTMLSelectElement> & { children: React.ReactNode }> = (props) => (
    <select {...props} className="w-full p-3 bg-base-200 border border-base-300 rounded-md focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition-shadow appearance-none bg-no-repeat bg-right pr-8" style={{backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%239ca3af' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`, backgroundPosition: 'right 0.5rem center', backgroundSize: '1.5em 1.5em' }}/>
);


const Toggle: React.FC<{checked: boolean, onChange: (e: React.ChangeEvent<HTMLInputElement>) => void, label: string, description: string}> = ({ checked, onChange, label, description }) => (
    <div className="flex items-center justify-between bg-base-200 p-3 rounded-md border border-base-300">
        <div>
            <span className="font-semibold text-content-100">{label}</span>
            <p className="text-sm text-content-200">{description}</p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" checked={checked} onChange={onChange} className="sr-only peer" />
            <div className="w-11 h-6 bg-base-300 rounded-full peer peer-focus:ring-2 peer-focus:ring-brand-secondary peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary"></div>
        </label>
    </div>
);

export const InputSection: React.FC<InputSectionProps> = ({
  userInput,
  onInputChange,
  onGenerate,
  onStop,
  isGenerating,
  useThinkingMode,
  setUseThinkingMode,
}) => {
  const [fileName, setFileName] = useState<string | null>(null);

  // When userInput prop changes (e.g., selecting history), reset fileName
  useEffect(() => {
    // Only reset if the content is not from a file upload (i.e., it's from history)
    if (fileName) {
        setFileName(null);
    }
  }, [userInput.cv]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    
    const updateCvContent = (text: string) => {
        onInputChange({ cv: text });
    };

    if (file.type === 'application/pdf') {
        const reader = new FileReader();
        reader.onload = async (event) => {
            try {
                if (!event.target?.result) throw new Error("File reading failed.");
                const typedArray = new Uint8Array(event.target.result as ArrayBuffer);
                const pdf = await pdfjsLib.getDocument(typedArray).promise;
                let fullText = '';
                for (let i = 1; i <= pdf.numPages; i++) {
                    const page = await pdf.getPage(i);
                    const textContent = await page.getTextContent();
                    const pageText = textContent.items.map(item => 'str' in item ? item.str : '').join(' ');
                    fullText += pageText + '\n';
                }
                updateCvContent(fullText.trim());
            } catch (error) {
                 console.error("Error reading PDF file:", error);
                 setFileName(`Error reading ${file.name}`);
                 updateCvContent('');
            }
        };
        reader.onerror = () => {
             console.error("Error reading file");
             setFileName("Error reading file");
        }
        reader.readAsArrayBuffer(file);
    } else {
        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target?.result as string;
            updateCvContent(text);
        };
        reader.onerror = () => {
            console.error("Error reading file");
            setFileName("Error reading file");
        }
        reader.readAsText(file);
    }
    // FIX: Reset the input value to allow uploading the same file again.
    e.target.value = '';
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <Label htmlFor="cv-upload">📄 Seu Currículo Atual</Label>
        <p className="text-xs text-content-200 mb-2 -mt-1">Cole ou faça upload do seu CV. Vamos otimizá-lo para a vaga que você deseja!</p>
        <label htmlFor="cv-upload" className="flex flex-col items-center justify-center w-full h-32 px-4 transition bg-base-200 border-2 border-base-300 border-dashed rounded-md appearance-none cursor-pointer hover:border-brand-primary focus:outline-none">
            {fileName ? (
                <div className="text-center">
                    <FileIcon className="w-8 h-8 mx-auto text-brand-success" />
                    <span className="font-medium text-content-100 break-all">{fileName}</span>
                    <p className="text-xs text-content-200">✓ Arquivo carregado. Clique para trocar.</p>
                </div>
            ) : (
                <div className="text-center">
                    <UploadIcon className="w-8 h-8 mx-auto text-brand-primary"/>
                    <span className="font-medium text-content-100">Clique para enviar seu currículo</span>
                    <p className="text-xs text-content-200">Aceito PDF, TXT ou MD</p>
                </div>
            )}
        </label>
        <input id="cv-upload" type="file" className="hidden" onChange={handleFileChange} accept=".txt,.md,text/plain,text/markdown,.pdf" />
        <TextArea 
            id="cv" 
            value={userInput.cv} 
            onChange={(e) => { 
                onInputChange({ cv: e.target.value });
                if (fileName) setFileName(null); 
            }} 
            required 
            className="mt-2 h-48" 
            placeholder="...ou cole todo o conteúdo do seu currículo aqui"
        />
      </div>
      <div>
        <Label htmlFor="jobUrl">🎯 Link da Vaga dos Seus Sonhos</Label>
        <p className="text-xs text-content-200 mb-2 -mt-1">Cole a URL da vaga (LinkedIn, Gupy, etc.). Vamos analisar todos os requisitos!</p>
        <TextInput 
            id="jobUrl" 
            type="url" 
            value={userInput.jobUrl} 
            onChange={(e) => onInputChange({ jobUrl: e.target.value })} 
            required 
            placeholder="https://www.linkedin.com/jobs/view/..."
        />
      </div>
       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="tone">💼 Tom da Candidatura</Label>
          <Select id="tone" value={userInput.tone} onChange={(e) => onInputChange({ tone: e.target.value })}>
            {['Profissional mas entusiasmado', 'Profissional', 'Formal', 'Confiante', 'Casual'].map(o => <option key={o} value={o}>{o}</option>)}
          </Select>
        </div>
        <div>
          <Label htmlFor="language">🌎 Idioma</Label>
          <Select id="language" value={userInput.language} onChange={(e) => onInputChange({ language: e.target.value })}>
            {['Português Brasileiro', 'Inglês', 'Espanhol'].map(o => <option key={o} value={o}>{o}</option>)}
          </Select>
        </div>
      </div>
      <div>
        <Label htmlFor="customContext">✨ Instruções Especiais (Opcional)</Label>
        <p className="text-xs text-content-200 mb-2 -mt-1">Quer destacar algo específico? Conte pra gente! Ex: "Enfatizar experiência com liderança"</p>
        <TextArea 
            id="customContext" 
            value={userInput.customContext} 
            onChange={(e) => onInputChange({ customContext: e.target.value })} 
            className="h-24" 
            placeholder="Ex: Quero destacar minha experiência com trabalho remoto e gestão de equipes distribuídas..."
        />
      </div>
      <div className="space-y-4">
        <Toggle
            checked={useThinkingMode}
            onChange={() => setUseThinkingMode(!useThinkingMode)}
            label="🧠 Modo Análise Profunda"
            description="Usa IA mais avançada para análises complexas. Leva mais tempo, mas gera resultados ainda melhores."
        />
        <button
          type="submit"
          disabled={isGenerating}
          className="w-full flex items-center justify-center gap-2 text-white font-bold py-4 px-6 rounded-lg bg-gradient-to-r from-brand-primary to-brand-secondary hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-base-100 focus:ring-brand-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
        >
          {isGenerating ? '⏳ Personalizando...' : '🚀 Criar Materiais Personalizados'}
        </button>
        {isGenerating && (
            <button
                type="button"
                onClick={onStop}
                className="w-full flex items-center justify-center gap-2 text-content-100 font-bold py-3 px-4 rounded-md bg-base-300 hover:bg-base-300/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-base-100 focus:ring-red-500 transition-colors"
            >
                <StopIcon className="w-5 h-5" />
                ⏸️ Parar Geração
            </button>
        )}
      </div>
    </form>
  );
};
