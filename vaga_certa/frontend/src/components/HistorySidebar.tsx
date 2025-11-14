import React, { useState, useRef, useEffect, useMemo } from 'react';
import type { HistoryItem } from '../types';
import { PlusIcon, PencilIcon, TrashIcon, CheckIcon, XIcon, ChevronRightIcon, ChevronDownIcon } from './Icons';

interface HistorySidebarProps {
  history: HistoryItem[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onUpdateTitle: (id: string, newTitle: string) => void;
}

const HistoryItemView: React.FC<{
    item: HistoryItem;
    isActive: boolean;
    isGrouped: boolean;
    onSelect: () => void;
    onDelete: () => void;
    onStartEdit: () => void;
}> = ({ item, isActive, isGrouped, onSelect, onDelete, onStartEdit }) => {
    return (
        <div 
            onClick={onSelect}
            className={`group flex justify-between items-center w-full text-left p-2.5 rounded-md cursor-pointer transition-colors ${
                isActive ? 'bg-brand-primary/20 text-content-100' : 'text-content-200 hover:bg-base-300/50'
            } ${isGrouped ? 'ml-4' : ''}`}
        >
            <span className="text-sm font-medium truncate pr-2 flex items-center gap-2">
                {item.isLoading && (
                    <svg className="animate-spin h-4 w-4 text-content-200" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                )}
                {item.title}
            </span>
            <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={(e) => { e.stopPropagation(); onStartEdit(); }} className="p-1 hover:text-content-100"><PencilIcon className="w-4 h-4" /></button>
                <button onClick={(e) => { e.stopPropagation(); onDelete(); }} className="p-1 hover:text-red-400"><TrashIcon className="w-4 h-4" /></button>
            </div>
        </div>
    );
};

const HistoryItemEdit: React.FC<{
    item: HistoryItem;
    isGrouped: boolean;
    onSave: (newTitle: string) => void;
    onCancel: () => void;
}> = ({ item, isGrouped, onSave, onCancel }) => {
    const [title, setTitle] = useState(item.title);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
    }, []);

    const handleSave = () => {
        if (title.trim()) {
            onSave(title.trim());
        }
    };

    return (
        <div className={`flex items-center w-full p-2 bg-base-300 rounded-md ${isGrouped ? 'ml-4' : ''}`}>
            <input 
                ref={inputRef}
                type="text" 
                value={title} 
                onChange={(e) => setTitle(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleSave(); if (e.key === 'Escape') onCancel(); }}
                onBlur={handleSave}
                className="text-sm bg-transparent outline-none ring-0 w-full text-content-100"
            />
            <button onClick={handleSave} className="p-1 text-green-400 hover:text-green-300"><CheckIcon className="w-4 h-4" /></button>
            <button onClick={onCancel} className="p-1 hover:text-content-100"><XIcon className="w-4 h-4" /></button>
        </div>
    );
};

export const HistorySidebar: React.FC<HistorySidebarProps> = ({
  history,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onUpdateTitle,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [expandedUrls, setExpandedUrls] = useState<Set<string>>(new Set());

  const groupedHistory = useMemo(() => {
    return history.reduce((acc, item) => {
        const key = item.userInput.jobUrl || `no-url-${item.id}`; // Group items with no URL separately
        if (!acc.has(key)) {
            acc.set(key, []);
        }
        acc.get(key)!.push(item);
        return acc;
    }, new Map<string, HistoryItem[]>());
  }, [history]);

  useEffect(() => {
    // Auto-expand the group of the active item
    const activeItem = history.find(item => item.id === activeId);
    if (activeItem?.userInput.jobUrl) {
        setExpandedUrls(prev => new Set(prev).add(activeItem.userInput.jobUrl));
    }
  }, [activeId, history]);


  const handleSaveTitle = (id: string, newTitle: string) => {
    onUpdateTitle(id, newTitle);
    setEditingId(null);
  };

  const toggleGroup = (url: string) => {
    setExpandedUrls(prev => {
        const newSet = new Set(prev);
        if (newSet.has(url)) {
            newSet.delete(url);
        } else {
            newSet.add(url);
        }
        return newSet;
    });
  };

  return (
    <aside className="w-72 bg-base-200 p-2 flex flex-col border-r border-base-300 h-full">
        <button onClick={onNew} className="flex items-center justify-center gap-2 w-full p-3 mb-3 text-sm font-bold text-white bg-gradient-to-r from-brand-primary to-brand-secondary hover:opacity-90 rounded-lg transition-all shadow-md hover:shadow-lg">
            <PlusIcon className="w-5 h-5" />
            ➕ Nova Candidatura
        </button>
        <div className="text-xs font-semibold text-content-200 px-2 mb-2 uppercase tracking-wide">📋 Histórico</div>
        <div className="flex-1 overflow-y-auto">
            <ul className="space-y-1">
                {Array.from(groupedHistory.entries()).map(([url, items]) => {
                    const isGroup = items.length > 1;
                    const groupTitle = `${items[0].title} (${items.length}x)`;
                    const isExpanded = expandedUrls.has(url);
                    
                    if (!isGroup) {
                        const item = items[0];
                        return (
                             <li key={item.id}>
                               {editingId === item.id ? (
                                   <HistoryItemEdit item={item} isGrouped={false} onSave={(newTitle) => handleSaveTitle(item.id, newTitle)} onCancel={() => setEditingId(null)} />
                               ) : (
                                   <HistoryItemView item={item} isActive={item.id === activeId} isGrouped={false} onSelect={() => onSelect(item.id)} onDelete={() => onDelete(item.id)} onStartEdit={() => setEditingId(item.id)} />
                               )}
                            </li>
                        );
                    }

                    return (
                        <li key={url}>
                            <div onClick={() => toggleGroup(url)} className="flex items-center gap-1 p-2.5 rounded-md cursor-pointer hover:bg-base-300/50">
                                {isExpanded ? <ChevronDownIcon className="w-4 h-4 flex-shrink-0"/> : <ChevronRightIcon className="w-4 h-4 flex-shrink-0"/>}
                                <span className="text-sm font-semibold truncate text-content-100">{groupTitle}</span>
                            </div>
                            {isExpanded && (
                                <ul className="space-y-1 mt-1">
                                    {items.map(item => (
                                        <li key={item.id}>
                                            {editingId === item.id ? (
                                                <HistoryItemEdit item={item} isGrouped={true} onSave={(newTitle) => handleSaveTitle(item.id, newTitle)} onCancel={() => setEditingId(null)} />
                                            ) : (
                                                <HistoryItemView item={item} isActive={item.id === activeId} isGrouped={true} onSelect={() => onSelect(item.id)} onDelete={() => onDelete(item.id)} onStartEdit={() => setEditingId(item.id)} />
                                            )}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </li>
                    )
                })}
            </ul>
        </div>
    </aside>
  );
};