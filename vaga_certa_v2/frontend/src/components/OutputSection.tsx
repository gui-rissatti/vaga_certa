import React, { useState } from 'react';
import type { GeneratedContent, CompatibilityInsights } from '../types';
import { CvIcon, CoverLetterIcon, MessageIcon, TipsIcon, CopyIcon, LinkIcon, DownloadIcon } from './Icons';
import { parseCvText } from '../utils/cvParser';
import { generateCvPdf } from '../utils/pdfGenerator';

type Tab = 'cv' | 'coverLetter' | 'message' | 'tips';

interface OutputSectionProps {
  content: GeneratedContent | null;
  isLoading: boolean;
  error: string | null;
  validationWarning?: string; // Warning quando score 30-70
  contentScore?: number; // Score de validação 0-100
}

const OutputPlaceholder: React.FC = () => (
  <div className="flex flex-col items-center justify-center h-full text-center p-8 border-2 border-dashed border-base-300 rounded-lg">
    <div className="text-6xl mb-4">🎯</div>
    <h3 className="text-xl font-semibold text-content-100 mb-2">Seus materiais personalizados aparecerão aqui</h3>
    <p className="text-content-200 max-w-md">Preencha seus dados à esquerda e clique em <strong className="text-brand-primary">"Criar Materiais Personalizados"</strong> para começar!</p>
    <p className="text-sm text-brand-secondary mt-4">💡 Dica: quanto mais detalhado seu CV, melhores os resultados!</p>
  </div>
);

const LoadingSpinner: React.FC = () => (
    <div className="flex flex-col items-center justify-center h-full text-center p-8 border-2 border-dashed border-base-300 rounded-lg">
        <svg className="animate-spin h-16 w-16 text-brand-primary mb-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <h3 className="text-xl font-semibold text-content-100 mb-2">✨ Criando seus materiais personalizados...</h3>
        <p className="text-content-200 mb-4">Estamos analisando a vaga e adaptando seu currículo. Isso leva alguns instantes.</p>
        <div className="flex gap-2 text-sm text-brand-secondary">
          <span>🔍 Analisando requisitos</span>
          <span>•</span>
          <span>✍️ Personalizando conteúdo</span>
        </div>
    </div>
);

const ErrorDisplay: React.FC<{ message: string }> = ({ message }) => {
    // BUG FIX: Garante que sempre exibimos uma string, não um objeto
    const displayMessage = typeof message === 'string' 
        ? message 
        : JSON.stringify(message, null, 2);
    
    return (
        <div className="flex flex-col items-center justify-center h-full text-center p-8 bg-red-900/20 border-2 border-dashed border-red-500/50 rounded-lg text-red-300">
            <div className="text-5xl mb-4">⚠️</div>
            <h3 className="text-lg font-semibold text-red-200 mb-2">Ops! Algo deu errado</h3>
            <p className="font-mono text-sm mt-2 bg-base-300/50 p-4 rounded max-w-lg whitespace-pre-wrap break-words">{displayMessage}</p>
            <p className="text-sm text-content-200 mt-4">💡 Tente novamente ou entre em contato com o suporte se o problema persistir.</p>
        </div>
    );
};

const ActionButton: React.FC<{ onClick: () => void; children: React.ReactNode; disabled?: boolean; }> = ({ onClick, children, disabled = false }) => (
    <button onClick={onClick} disabled={disabled} className="p-2 bg-base-300/50 rounded-md hover:bg-base-300 text-content-200 hover:text-content-100 transition disabled:opacity-50 disabled:cursor-not-allowed">
        {children}
    </button>
);

const clampScore = (score: number | undefined): number => {
  if (typeof score !== 'number' || Number.isNaN(score)) {
    return 0;
  }
  return Math.min(100, Math.max(0, Math.round(score)));
};

const scoreColor = (score: number): string => {
  if (score >= 75) return 'text-emerald-400';
  if (score >= 45) return 'text-amber-300';
  return 'text-rose-400';
};

const CompatibilityWidget: React.FC<{ data: CompatibilityInsights }> = ({ data }) => {
  const safeScore = clampScore(data.score);
  const gradient = 'linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #22c55e 100%)';

  return (
    <div className="px-4 pt-4">
      <div className="bg-base-100/60 border border-base-300 rounded-lg p-4 shadow-sm">
        <div className="flex flex-col items-center text-center gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-content-300">Compatibilidade com a vaga</p>
            <p className="text-sm text-content-200 mt-1">{data.label}</p>
          </div>
          <div className={`text-4xl font-semibold ${scoreColor(safeScore)}`}>
            {safeScore}%
          </div>
        </div>
        <div className="mt-4 h-2 rounded-full bg-base-300">
          <div
            className="h-2 rounded-full transition-all duration-500"
            style={{ width: `${safeScore}%`, backgroundImage: gradient }}
          />
        </div>
      </div>
    </div>
  );
};

const ValidationWarningBanner: React.FC<{ warning: string; score: number }> = ({ warning, score }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="px-4 pt-4">
      <div 
        className="bg-amber-900/20 border border-amber-600/50 rounded-lg p-3 shadow-sm relative cursor-help"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <div className="flex items-start gap-3">
          <div className="text-amber-400 text-xl flex-shrink-0">⚠️</div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-200 mb-1">
              Atenção: Vaga com poucos detalhes (Score: {score}/100)
            </p>
            <p className="text-xs text-amber-300/90">
              Os materiais foram gerados, mas podem ser menos precisos devido à falta de informações detalhadas na vaga.
            </p>
          </div>
        </div>
        {showTooltip && (
          <div className="absolute z-10 bottom-full left-0 right-0 mb-2 p-3 bg-base-100 border border-base-300 rounded-lg shadow-lg text-xs text-content-200">
            <p className="font-semibold mb-1">Detalhes da validação:</p>
            <p className="whitespace-pre-wrap">{warning}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export const OutputSection: React.FC<OutputSectionProps> = ({ 
  content, 
  isLoading, 
  error, 
  validationWarning, 
  contentScore 
}) => {
  const [activeTab, setActiveTab] = useState<Tab>('cv');
  const [copied, setCopied] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);


  const handleCopy = (textToCopy: string) => {
    navigator.clipboard.writeText(textToCopy).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleDownload = async (cvText: string) => {
    setIsDownloading(true);
    try {
        const parsedCv = parseCvText(cvText);
        await generateCvPdf(parsedCv);
    } catch (e) {
        console.error("Failed to generate PDF", e);
        alert(`Failed to generate PDF: ${e instanceof Error ? e.message : 'Unknown error'}`);
    } finally {
        setIsDownloading(false);
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay message={error} />;
  if (!content) return <OutputPlaceholder />;

  const tabs = [
    { id: 'cv', label: '📄 CV Otimizado', icon: <CvIcon /> },
    { id: 'coverLetter', label: '✉️ Carta de Apresentação', icon: <CoverLetterIcon /> },
    { id: 'message', label: '💼 Mensagem de Networking', icon: <MessageIcon /> },
    { id: 'tips', label: '🎤 Dicas para Entrevista', icon: <TipsIcon /> },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'cv': return content.optimizedCv;
      case 'coverLetter': return content.coverLetter;
      case 'message': return content.networkingMessage;
      case 'tips': return content.interviewTips;
      default: return '';
    }
  };

  const currentContent = renderContent();

  return (
    <div className="bg-base-200 rounded-lg shadow-lg h-[calc(100vh-10rem)] lg:h-auto lg:min-h-[500px] flex flex-col mt-8 lg:mt-0">
      {validationWarning && contentScore !== undefined && (
        <ValidationWarningBanner warning={validationWarning} score={contentScore} />
      )}
      {content.compatibility && <CompatibilityWidget data={content.compatibility} />}
      <div className="flex border-b border-base-300">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as Tab)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
              activeTab === tab.id
                ? 'border-brand-primary text-content-100'
                : 'border-transparent text-content-200 hover:bg-base-300/50'
            }`}
          >
            {tab.icon}
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>
      <div className="p-1 relative flex-grow overflow-hidden">
        <div className="bg-base-100 rounded-md h-full overflow-auto p-4 relative">
          <div className="absolute top-3 right-3 flex gap-2">
            {activeTab === 'cv' && (
                <ActionButton onClick={() => handleDownload(currentContent)} disabled={isDownloading}>
                    {isDownloading ? '...' : <DownloadIcon className="w-5 h-5" />}
                </ActionButton>
            )}
            <ActionButton onClick={() => handleCopy(currentContent)}>
                {copied ? 'Copiado!' : <CopyIcon className="w-5 h-5"/>}
            </ActionButton>
          </div>
          <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-content-200">
            {currentContent}
          </pre>
          {activeTab === 'tips' && content.sources.length > 0 && (
            <div className="mt-6 pt-4 border-t border-base-300">
              <h4 className="text-md font-semibold text-content-100 mb-2 flex items-center gap-2">
                <LinkIcon className="w-5 h-5" />
                Fontes da Pesquisa Google
              </h4>
              <ul className="space-y-2">
                {content.sources.map((source, index) => (
                  <li key={index}>
                    <a
                      href={source.uri}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-brand-secondary hover:underline break-all"
                    >
                      {source.title || source.uri}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};