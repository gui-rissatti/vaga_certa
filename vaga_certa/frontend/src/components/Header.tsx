
import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="bg-base-200 border-b border-base-300 p-4 shadow-md">
      <div className="container mx-auto flex items-center gap-4">
        <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br from-brand-primary to-brand-secondary">
          <span className="text-2xl font-bold text-white">VC</span>
        </div>
        <div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-brand-primary to-brand-secondary">
            Vaga Certa
          </h1>
          <p className="text-sm text-content-200">
            Seu próximo emprego começa aqui
          </p>
        </div>
      </div>
    </header>
  );
};

