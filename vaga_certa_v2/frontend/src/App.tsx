
import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { InputSection } from './components/InputSection';
import { OutputSection } from './components/OutputSection';
import { HistorySidebar } from './components/HistorySidebar';
import { generateCareerMaterials, extractJobTitleAndCompany, extractJobContentFromUrl } from './services/apiService';
import type { UserInput, HistoryItem } from './types';

const defaultUserInput: UserInput = {
  cv: `João Silva
Engenheiro de Software Sênior
São Paulo, SP | (11) 98765-4321 | joao.silva@email.com | linkedin.com/in/joaosilva

Resumo
Engenheiro de Software Sênior orientado a resultados, com mais de 8 anos de experiência no design, desenvolvimento e implantação de aplicações web escaláveis. Proficiente em React, Node.js e tecnologias cloud. Apaixonado por construir software de alta qualidade e liderar equipes rumo ao sucesso.

Experiência
Tech Solutions Brasil - São Paulo, SP
Engenheiro de Software Sênior, 2018 - Presente
- Liderei equipe de 4 engenheiros no desenvolvimento de nova plataforma e-commerce, resultando em aumento de 30% nas vendas.
- Arquitetei e implementei backend baseado em microserviços usando Node.js e Docker.
- Melhorei performance da aplicação em 40% através de otimização de código e tuning de banco de dados.

Inovadores Web - Rio de Janeiro, RJ
Engenheiro de Software, 2015 - 2018
- Desenvolvi e mantive componentes front-end utilizando React e Redux.
- Colaborei com equipes multifuncionais para entregar novas funcionalidades no prazo.

Educação
Universidade Federal de São Paulo
Bacharelado em Ciência da Computação, 2015`,
  jobUrl: `https://linkedin.com/jobs/view/3933223639`,
  tone: 'Profissional mas entusiasmado',
  language: 'Português Brasileiro',
  customContext: `Quero que a empresa perceba que temos boa compatibilidade; adicione tecnologias da stack caso haja alguma estritamente necessária que não tenha listado na descrição da vaga; Maximize minhas chances com ATS e palavras-chave.`,
};

const STORAGE_KEY = 'career-copilot-history';

const App: React.FC = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [activeHistoryId, setActiveHistoryId] = useState<string | null>(null);
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [useThinkingMode, setUseThinkingMode] = useState<boolean>(false);
  const [currentInput, setCurrentInput] = useState<UserInput>(defaultUserInput);
  const generationCancelledRef = useRef(false);

  useEffect(() => {
    try {
      const storedHistory = localStorage.getItem(STORAGE_KEY);
      if (storedHistory) {
        const parsedHistory = (JSON.parse(storedHistory) as HistoryItem[]).filter(item => !item.isLoading);
        setHistory(parsedHistory);
        if (parsedHistory.length === 0) {
            setCurrentInput(defaultUserInput);
        }
      }
    } catch (e) {
      console.error("Failed to load history from localStorage", e);
    }
  }, []);

  useEffect(() => {
    try {
      const historyToSave = history.filter(item => !item.isLoading);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(historyToSave));
    } catch (e) {
      console.error("Failed to save history to localStorage", e);
    }
  }, [history]);

  const handleStop = useCallback(() => {
    generationCancelledRef.current = true;
    const id = generatingId;
    if (id) {
      setHistory(prev => prev.map(item =>
        item.id === id
          ? { ...item, isLoading: false, error: "⏸️ Você interrompeu a geração. Tudo bem! Você pode tentar novamente quando quiser." }
          : item
      ));
      setGeneratingId(null);
    }
  }, [generatingId]);

  const handleGenerate = useCallback(async () => {
    if (generatingId) return;
    
    const input = currentInput;
    generationCancelledRef.current = false;
    
    const activeItem = history.find(h => h.id === activeHistoryId);
    const isUpdatingActiveItem = activeItem && !activeItem.generatedContent && !activeItem.isLoading;

    const idToProcess = isUpdatingActiveItem ? activeHistoryId! : Date.now().toString();
    setGeneratingId(idToProcess);

    const updateHistoryItem = (id: string, updates: Partial<HistoryItem>) => {
        setHistory(prev => prev.map(item => item.id === id ? { ...item, ...updates } : item));
    };

    if (isUpdatingActiveItem) {
        updateHistoryItem(idToProcess, { userInput: input, isLoading: true, error: null, title: '🔍 Analisando a vaga...' });
    } else {
        const newHistoryItem: HistoryItem = {
            id: idToProcess,
            title: '🔍 Analisando a vaga...',
            userInput: input,
            generatedContent: null,
            isLoading: true,
            error: null,
        };
        setHistory(prev => [newHistoryItem, ...prev]);
        setActiveHistoryId(idToProcess);
    }
    
    try {
        // Step 1: Extract content directly from URL using web scraping (ONLY method - no AI fallback)
        const jobContent = await extractJobContentFromUrl(input.jobUrl);
        if (generationCancelledRef.current) return;
        
        updateHistoryItem(idToProcess, { error: '📊 Identificando requisitos...' });

        // Step 2: Extract Title and Company using web scraping (ONLY method - no AI fallback)
        const extractionResult = await extractJobTitleAndCompany(jobContent, input.jobUrl);
        if (generationCancelledRef.current) return;

        const finalTitle = `${extractionResult.company} - ${extractionResult.jobTitle}`;
        const jobDetails: JobDetails = {
          jobTitle: extractionResult.jobTitle,
          company: extractionResult.company,
          jobDescription: jobContent,
          contentScore: extractionResult.contentScore,
          validationWarning: extractionResult.validationWarning,
        };
        
        updateHistoryItem(idToProcess, { title: finalTitle, error: '✍️ Personalizando seus materiais...' });

        // Step 3: Generate Career Materials using AI (AI is ONLY used here for content generation)
        const result = await generateCareerMaterials(
            input,
            jobDetails,
            useThinkingMode
        );
        if (generationCancelledRef.current) return;

        updateHistoryItem(idToProcess, { 
          generatedContent: result, 
          isLoading: false, 
          error: null,
          jobDetails
        });

    } catch (e) {
        if (generationCancelledRef.current) return;
        
        // BUG FIX: Garante que a mensagem de erro é sempre uma string legível
        let message: string;
        
        if (e instanceof Error) {
            message = e.message;
        } else if (typeof e === 'object' && e !== null) {
            // Se for um objeto, tenta extrair propriedades comuns de erro
            const errorObj = e as any;
            message = errorObj.message || errorObj.detail || errorObj.error || JSON.stringify(e);
        } else {
            message = String(e) || 'Ops! Algo inesperado aconteceu.';
        }
        
        // Adiciona sugestão de fallback manual para erros de scraping
        if (message.includes('Web scraper') || message.includes('VALIDAÇÃO FALHOU') || message.includes('não conseguiu extrair')) {
          message += '\n\n💡 DICA: Tente copiar e colar a descrição da vaga diretamente no campo de texto, ao invés de usar o link. Às vezes isso funciona melhor!';
        }
        
        updateHistoryItem(idToProcess, { 
          error: message, 
          isLoading: false, 
          title: '⚠️ Não conseguimos processar esta vaga' 
        });
    } finally {
        setGeneratingId(curr => (curr === idToProcess ? null : curr));
    }
  }, [generatingId, useThinkingMode, currentInput, history, activeHistoryId]);

  const handleSelectHistory = (id: string) => {
    const selectedItem = history.find(item => item.id === id);
    if (selectedItem) {
        setActiveHistoryId(id);
        setCurrentInput(selectedItem.userInput);
    }
  };

  const handleNewApplication = () => {
    const newId = Date.now().toString();
    const newDraftItem: HistoryItem = {
      id: newId,
      title: "✨ Nova Candidatura (Rascunho)",
      userInput: defaultUserInput,
      generatedContent: null,
      isLoading: false,
      error: null,
    };
    setHistory(prev => [newDraftItem, ...prev]);
    setActiveHistoryId(newId);
    setCurrentInput(defaultUserInput);
  }

  const handleDeleteHistory = (id: string) => {
    setHistory(prev => {
        const newHistory = prev.filter(item => item.id !== id);
        if (activeHistoryId === id) {
            if (newHistory.length > 0) {
              setActiveHistoryId(newHistory[0].id);
              setCurrentInput(newHistory[0].userInput);
            } else {
              setActiveHistoryId(null);
              setCurrentInput(defaultUserInput);
            }
        }
        return newHistory;
    });
  };

  const handleUpdateTitle = (id: string, newTitle: string) => {
    setHistory(prev => prev.map(item => item.id === id ? { ...item, title: newTitle } : item));
  };
  
  const handleInputChange = (newInput: Partial<UserInput>) => {
    setCurrentInput(prev => ({ ...prev, ...newInput }));
  };

  const activeItem = history.find(item => item.id === activeHistoryId);

  return (
    <div className="flex h-full font-sans bg-base-100 text-content-200">
      <HistorySidebar
        history={history}
        activeId={activeHistoryId}
        onSelect={handleSelectHistory}
        onNew={handleNewApplication}
        onDelete={handleDeleteHistory}
        onUpdateTitle={handleUpdateTitle}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <div className="container mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 lg:gap-8">
              <InputSection
                userInput={currentInput}
                onInputChange={handleInputChange}
                onGenerate={handleGenerate}
                onStop={handleStop}
                isGenerating={!!generatingId}
                useThinkingMode={useThinkingMode}
                setUseThinkingMode={setUseThinkingMode}
              />
              <OutputSection
                content={activeItem?.generatedContent ?? null}
                isLoading={activeItem?.isLoading ?? false}
                error={activeItem?.error ?? null}
                validationWarning={activeItem?.jobDetails?.validationWarning}
                contentScore={activeItem?.jobDetails?.contentScore}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
